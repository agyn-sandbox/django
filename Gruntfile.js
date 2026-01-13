'use strict';

const globalThreshold = 50; // Global code coverage threshold (as a percentage)
const isCI = process.env.CI === 'true';
const puppeteerExecutable = process.env.PUPPETEER_EXECUTABLE_PATH;

module.exports = function(grunt) {
    grunt.initConfig({
        qunit: {
            options: {
                puppeteer: {
                    args: isCI ? ['--no-sandbox', '--disable-setuid-sandbox'] : [],
                    executablePath: puppeteerExecutable,
                }
            },
            all: ['js_tests/tests.html']
        }
    });

    grunt.loadNpmTasks('grunt-contrib-qunit');
    grunt.registerTask('test', ['qunit']);
    grunt.registerTask('default', ['test']);
};
