module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
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
    }
  });

  grunt.loadNpmTasks('grunt-karma');
  grunt.loadNpmTasks('grunt-karma-coveralls');

  // Default task(s).
  grunt.registerTask('default', ['karma:unit', 'coveralls']);

};