from asgiref.sync import sync_to_async
from django.test import TestCase

from .models import (
    AsyncAuthor,
    AsyncBook,
    AsyncGroup,
    GenericArticle,
    GenericNote,
    GroupMembership,
)


class AsyncRelatedManagerTests(TestCase):
    async def test_reverse_fk_acreate_injects_foreign_key(self):
        author = await AsyncAuthor.objects.acreate(name="Author")

        book = await author.books.acreate(title="Async Book", pages=200)

        self.assertEqual(book.author_id, author.pk)
        stored = await AsyncBook.objects.aget(pk=book.pk)
        self.assertEqual(stored.author_id, author.pk)
        self.assertEqual(stored.pages, 200)

    async def test_reverse_fk_acreate_unsaved_parent_error(self):
        author = AsyncAuthor(name="Ghost")
        msg = (
            f'"{author!r}" needs to have a value for field "id" before '
            "this relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            await author.books.acreate(title="Should fail")

    async def test_reverse_fk_aget_or_create_respects_relation(self):
        author = await AsyncAuthor.objects.acreate(name="Author")

        book, created = await author.books.aget_or_create(title="Existing Book")
        self.assertIs(created, True)
        self.assertEqual(book.author_id, author.pk)

        same_book, created_again = await author.books.aget_or_create(
            title="Existing Book"
        )
        self.assertIs(created_again, False)
        self.assertEqual(same_book.pk, book.pk)

    async def test_reverse_fk_aupdate_or_create_updates_instance(self):
        author = await AsyncAuthor.objects.acreate(name="Author")

        book, created = await author.books.aupdate_or_create(
            title="Versioned Book", defaults={"pages": 150}
        )
        self.assertIs(created, True)
        self.assertEqual(book.author_id, author.pk)
        self.assertEqual(book.pages, 150)

        updated_book, created_again = await author.books.aupdate_or_create(
            title="Versioned Book", defaults={"pages": 175}
        )
        self.assertIs(created_again, False)
        self.assertEqual(updated_book.pk, book.pk)
        self.assertEqual(updated_book.pages, 175)
        refreshed = await AsyncBook.objects.aget(pk=book.pk)
        self.assertEqual(refreshed.pages, 175)
        self.assertEqual(refreshed.author_id, author.pk)

    async def test_m2m_acreate_links_instance_and_through_defaults(self):
        group = await AsyncGroup.objects.acreate(name="Group")

        member = await group.members.acreate(
            name="Alice", title="Engineer", through_defaults={"note": "invite"}
        )

        self.assertEqual(member.title, "Engineer")
        self.assertEqual(await group.members.acount(), 1)
        membership = await GroupMembership.objects.aget(group=group, member=member)
        self.assertEqual(membership.note, "invite")

    async def test_m2m_aget_or_create_retains_existing_membership(self):
        group = await AsyncGroup.objects.acreate(name="Group")

        member, created = await group.members.aget_or_create(
            name="Bob",
            defaults={"title": "Member"},
            through_defaults={"note": "init"},
        )
        self.assertIs(created, True)

        membership = await GroupMembership.objects.aget(group=group, member=member)
        self.assertEqual(membership.note, "init")

        same_member, created_again = await group.members.aget_or_create(
            name="Bob",
            defaults={"title": "Member"},
            through_defaults={"note": "ignored"},
        )
        self.assertIs(created_again, False)
        self.assertEqual(same_member.pk, member.pk)
        self.assertEqual(await group.members.acount(), 1)
        membership_refreshed = await GroupMembership.objects.aget(
            group=group, member=member
        )
        self.assertEqual(membership_refreshed.note, "init")

    async def test_m2m_aupdate_or_create_updates_member_and_keeps_relation(self):
        group = await AsyncGroup.objects.acreate(name="Group")

        member, created = await group.members.aupdate_or_create(
            name="Cara",
            defaults={"title": "Member"},
            through_defaults={"note": "initial"},
        )
        self.assertIs(created, True)

        membership = await GroupMembership.objects.aget(group=group, member=member)
        self.assertEqual(membership.note, "initial")

        updated_member, created_again = await group.members.aupdate_or_create(
            name="Cara",
            defaults={"title": "Lead"},
            through_defaults={"note": "later"},
        )
        self.assertIs(created_again, False)
        self.assertEqual(updated_member.pk, member.pk)
        self.assertEqual(updated_member.title, "Lead")
        self.assertEqual(await group.members.acount(), 1)
        preserved_membership = await GroupMembership.objects.aget(
            group=group, member=member
        )
        self.assertEqual(preserved_membership.note, "initial")

    async def test_generic_acreate_sets_content_fields(self):
        article = await GenericArticle.objects.acreate(name="Article")
        notes_manager = await sync_to_async(getattr)(article, "notes")

        note = await notes_manager.acreate(message="hello", extra="first")

        self.assertEqual(await notes_manager.acount(), 1)
        stored = await GenericNote.objects.aget(pk=note.pk)
        self.assertEqual(stored.object_id, article.pk)
        related = await notes_manager.aget(pk=note.pk)
        self.assertEqual(related.pk, note.pk)

    async def test_generic_aget_or_create_returns_existing(self):
        article = await GenericArticle.objects.acreate(name="Article")
        notes_manager = await sync_to_async(getattr)(article, "notes")

        note, created = await notes_manager.aget_or_create(message="unique")
        self.assertIs(created, True)

        same_note, created_again = await notes_manager.aget_or_create(message="unique")
        self.assertIs(created_again, False)
        self.assertEqual(same_note.pk, note.pk)

    async def test_generic_aupdate_or_create_updates_existing(self):
        article = await GenericArticle.objects.acreate(name="Article")
        notes_manager = await sync_to_async(getattr)(article, "notes")

        note, created = await notes_manager.aupdate_or_create(
            message="tracked", defaults={"extra": "v1"}
        )
        self.assertIs(created, True)
        self.assertEqual(note.extra, "v1")

        updated_note, created_again = await notes_manager.aupdate_or_create(
            message="tracked", defaults={"extra": "v2"}
        )
        self.assertIs(created_again, False)
        self.assertEqual(updated_note.pk, note.pk)
        self.assertEqual(updated_note.extra, "v2")
        stored = await notes_manager.aget(message="tracked")
        self.assertEqual(stored.extra, "v2")
