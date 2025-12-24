# ADR: Edit-only ModelFormSet mode

Context: Users need a robust way to present an edit-only ModelFormSet that allows editing and optional deletion of existing objects but strictly disallows creation of new objects. Current patterns (e.g., using extra=0, max_num=0, validate_max=True) are insufficient because client-side JavaScript can add forms and POST payloads can tamper with ManagementForm fields (TOTAL_FORMS, INITIAL_FORMS). This ADR specifies an explicit API and server-side validation to enforce edit-only behavior.

Decision: Introduce a first-class flag on BaseModelFormSet and the model formset factories to disable creation of new objects, independent of client-submitted ManagementForm values.

Summary
- New flag: allow_create (bool), default True. When False, the formset operates in edit-only mode.
- Optional alias: edit_only (bool), default False, sugar for allow_create=False. Only one source of truth is persisted (allow_create).
- Enforce server-side invariants that do not trust ManagementForm INITIAL_FORMS for edit-only classification.
- Save behavior never calls save_new() when allow_create=False; instead, raise a ValidationError on attempts to submit extra/new forms.

API Proposal
- Add parameter allow_create to:
  - django.forms.models.modelformset_factory(..., allow_create: bool = True, ...)
  - django.forms.models.inlineformset_factory(..., allow_create: bool = True, ...)
  - django.forms.models.BaseModelFormSet.__init__(..., allow_create: bool = True, ...)
- Optional alias edit_only (default False) accepted by the same entry points; internally translated to allow_create = not edit_only.
- Backwards-compatible default: omit the flag to preserve current behavior.

Validation and Save Behavior
1) Classification independent of client INITIAL_FORMS
   - In BaseModelFormSet.initial_form_count():
     - If allow_create is False, return len(self.get_queryset()) even when bound.
     - Otherwise, keep existing behavior (use ManagementForm.cleaned_data[INITIAL_FORMS] when bound).
   - Rationale: Prevent tampering with INITIAL_FORMS from reclassifying posted forms.

2) Extra form submission is rejected in edit-only mode
   - In BaseModelFormSet.clean():
     - Call super().clean() (to retain validate_unique and other inherited behaviors).
     - If allow_create is False:
       - Compute changed_extra = [f for f in self.extra_forms if f.has_changed() and not (self.can_delete and self._should_delete_form(f))].
       - If changed_extra is non-empty, raise ValidationError with code='add_not_allowed' and message: "Adding new objects is not allowed in this formset.".
       - Note: This tolerates empty extra forms posted by clients (e.g., TOTAL_FORMS greater than expected) but enforces that they’re empty or marked for deletion.

3) save() never creates new objects in edit-only mode
   - In BaseModelFormSet.save_new_objects():
     - If allow_create is False:
       - If any extra form has changed and is not marked for deletion, raise ValidationError(code='add_not_allowed').
       - Return [] (no new objects).
   - In BaseModelFormSet.save():
     - Keep existing orchestration, but the save_new_objects() guard ensures no new objects are created even if save() is called without prior is_valid().

4) Prevent editing objects outside the provided queryset
   - Preserve current behavior:
     - BaseModelFormSet._construct_form() binds instances by PK only if pk belongs to self.get_queryset(); otherwise, the form’s instance remains new (instance.pk is None).
     - BaseModelFormSet.save_existing_objects() skips forms whose instance.pk is None. No new objects are created or edited in this path.
   - Tests will assert that posting PKs not in the queryset does not lead to creation or modification of out-of-scope objects.

5) Deletions
   - Deletions remain controlled by can_delete / can_delete_extra.
   - Recommended default: allow deletions (can_delete=True) is orthogonal to allow_create. Edit-only means "no creation"; editing and deletion behavior follow existing configuration.
   - Behavior: In edit-only mode, extra forms marked for deletion are ignored (no-op).

6) Interaction with extra, max_num, validate_max, min_num, absolute_max
   - When allow_create is False:
     - Rendering (unbound): Force extra=0 to avoid presenting add forms. Precedence: edit-only overrides any explicit extra > 0.
     - Bound post: total_form_count still uses ManagementForm’s TOTAL_FORMS (with absolute_max cap). Edit-only validation tolerates empty extra forms but rejects changed ones.
     - validate_max / max_num: Unchanged behavior; if validate_max is True and clients post more than max_num forms, the existing 'too_many_forms' error may be raised in addition to 'add_not_allowed'. If max_num is set lower than len(queryset), existing behavior applies (initial forms are still displayed).
     - min_num / validate_min: Unchanged and orthogonal. Edit-only does not force a minimum number of changed forms.
     - absolute_max: Unchanged; continues to protect against memory exhaustion. Edit-only logic runs after ManagementForm is cleaned.

7) Error messages and codes
   - BaseModelFormSet.default_error_messages augmented with:
     - 'add_not_allowed': _('Adding new objects is not allowed in this formset.')
   - ValidationError raised at formset.clean() and/or save_new_objects() uses this code/message.

Concrete Implementation Outline (code paths)
- django/forms/models.py:
  - class BaseModelFormSet:
    - __init__: accept allow_create and optional edit_only; set self.allow_create accordingly and store self.initial_extra.
    - initial_form_count(): if self.allow_create is False, return len(self.get_queryset()) regardless of is_bound.
    - clean(): call super().clean(); enforce changed_extra validation (add_not_allowed) when allow_create is False.
    - save_new_objects(): enforce add_not_allowed and return [] when allow_create is False.
  - modelformset_factory(...): accept allow_create (and edit_only alias); if allow_create is False, set extra=0 for the returned FormSet type; propagate allow_create into the constructed FormSet via formset attrs or __init__ kwargs.
  - inlineformset_factory(...): same as above.
- django/forms/formsets.py:
  - No changes required for core mechanisms; behavior remains compatible. Optionally add 'add_not_allowed' in BaseFormSet.default_error_messages if shared by subclasses.
- docs/topics/forms/modelforms.txt:
  - Replace the note that "formsets don’t yet provide functionality for an edit-only view" (ticket 26142) with guidance on the new flag. Include rationale why extra=0 is insufficient.

Server-side Invariants (edit-only)
- initial_form_count = len(queryset), independent of client INITIAL_FORMS.
- For i >= initial_form_count, any form with has_changed() and not marked for deletion causes a ValidationError at clean() and save().
- save() must not call save_new(); save_new_objects() raises if any attempt is made.
- Objects outside queryset are not edited, and no new object is created from such data.

Test Plan (unit tests)
1) Reproduce vulnerabilities with current behavior (flag absent)
   - Case A: extra=0, client posts a payload with TOTAL_FORMS = initial_count + 1 and provides data for the extra form; assert new object is created (pre-flag behavior).
   - Case B: max_num=0, validate_max=True, client tampers with INITIAL_FORMS to reclassify forms; assert new object can be created (pre-flag behavior).

2) Edit-only prevents creation
   - With allow_create=False (or edit_only=True), repeat Case A and Case B:
     - is_valid() returns False with non-form error code='add_not_allowed' when extra forms contain changes.
     - save() raises ValidationError(code='add_not_allowed') if called directly without validation, and no objects are created.

3) Successful editing of existing queryset objects
   - Provide changes to one or more initial forms; assert is_valid() is True and save() updates those instances; no additions.

4) Bogus PKs, blank PKs, PKs outside queryset
   - Submit initial-index forms whose posted PKs are invalid, blank, or outside the queryset:
     - Assert that those forms either error due to required PK (invalid/blank) or are treated as non-existent instances with instance.pk=None and thus skipped by save_existing_objects.
     - Assert that no new objects are created and appropriate errors surface for required PKs.

5) Deletion behavior
   - With can_delete=True and allow_create=False, mark initial forms for deletion:
     - Assert is_valid() is True and save() deletes those objects.
   - Mark extra forms for deletion and submit changes:
     - Assert is_valid() is True and those extra forms are ignored (no object creation and no deletion of non-existent objects).

6) Interaction with max_num/validate_max/extra
   - With allow_create=False and explicit extra>0 passed to factory:
     - Assert rendered unbound formset has no add forms (extra=0 enforced).
   - With allow_create=False and validate_max=True, max_num<N forms posted:
     - Assert too_many_forms error appears alongside add_not_allowed when applicable; no object creation.

Documentation Updates Outline
- Update docs/topics/forms/modelforms.txt:
  - New section: "Edit-only model formsets" describing allow_create=False (and edit_only=True alias).
  - Explain why extra=0 and max_num=0 are insufficient; show POST manipulation examples.
  - Provide usage examples:
    - AuthorFormSet = modelformset_factory(Author, fields=(...), allow_create=False, can_delete=True)
    - Inline formset equivalent.
  - Describe error messaging and interaction with deletion.

Backwards Compatibility
- Defaults preserve existing behavior: allow_create defaults to True.
- No changes to ManagementForm or BaseFormSet semantics for non-edit-only formsets.
- Existing code continues to work without modification; edit-only must be explicitly opted in.

References
- Django docs (current): docs/topics/forms/modelforms.txt states lack of edit-only functionality and references ticket #26142.
- Relevant code paths and behaviors analyzed:
  - django/forms/formsets.py: ManagementForm, BaseFormSet.initial_form_count(), total_form_count(), extra_forms, full_clean(), validate_max.
  - django/forms/models.py: BaseModelFormSet.initial_form_count(), _construct_form(), save_existing_objects(), save_new_objects(), add_fields(), modelformset_factory(), inlineformset_factory().

Consequences
- Provides a secure, explicit server-side control to prevent new object creation via formsets.
- Minimal, localized changes to BaseModelFormSet and factories; no changes to core formset mechanics.
- Clear tests and documentation to support and enforce expected behavior.
