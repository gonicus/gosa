module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    banner: '/*\n'+
            ' *\n'+
            ' * This file is part of the GOsa project -  http://gosa-project.org\n'+
            ' *\n'+
            ' * Copyright:\n'+
            ' *  (C) 2010-<%= grunt.template.today("yyyy") %> GONICUS GmbH, Germany, http://www.gonicus.de\n'+
            ' *\n'+
            ' * License:\n'+
            ' *  LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html\n'+
            ' *\n'+
            ' * See the LICENSE file in the project\'s top-level directory for details.\n'+
            ' */\n',

    coveralls: {
      options: {
        debug: true,
        coverageDir: 'coverage',
        dryRun: true,
        force: true,
        recursive: true
      }
    },
    karma: {
      unit : {
        configFile : 'karma.conf.js'
      }
    },
    usebanner: {
      dist: {
        options: {
          position: 'top',
          replace: /\/\*=+\n[\n\w\W]+\s*=+\s\*\/\n*/,
          linebreak: true,
          banner: '<%= banner %>'
        },
        files: {
          src: [ 'source/class/**/*.js' ]
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-karma');
  grunt.loadNpmTasks('grunt-karma-coveralls');
  grunt.loadNpmTasks('grunt-banner');

  // Default task(s).
  grunt.registerTask('default', ['karma:unit', 'coveralls']);

};