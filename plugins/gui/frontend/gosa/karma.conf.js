// Karma configuration
// Generated on Mon Apr 11 2016 10:15:49 GMT+0200 (CEST)
/**
* This is the qooxdoo adapter for karma. It adds the required files needed to run your tests to the karma configuration automatically.
* You can use two different test runners: qooxdoo and jasmine. With jasmine you can write your tests in the jasmine syntax. But there is
* one caveheat which you have to obey: Since qooxdoo's generator does not understand the jasmine syntax you cannot generate the 'test' and 'test-source' jobs.
* The good thing is that you do not have to. Once you generated the 'source' version of your qooxdoo application (./generate source) your tests will run.
* Currently you can only run the tests in source with the jasmine test runner. The build will not work with jasmine.
*
* The necessary settings for using jasmine are:
* frameworks: ['qooxdoo', 'jasmine'],
* files: [<paths to your jasmine test specs>]
* qooxdooFramework: {
*   testSources: true
* }
*/
var path = require('path');

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    // if you only use the qooxdoo framework, qooxdoo's testrunner is used to run the tests
    // but you can also use the jasmine testrunner to run your tests
    // frameworks: ['qooxdoo', 'jasmine']
    frameworks: ['qooxdoo'],


    // list of files / patterns to load in the browser => auto-filled by the qooxdoo adapter
    // if you use the jasmine testrunner, you have to add you test spec files here
    files: [],


    // list of files to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      'source/class/gosa/{*.js,!(test)/**/*.js}': 'coverage'
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress', 'coverage'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Chrome'],

    client: {
      captureConsole: false
    },

    browserNoActivityTimeout: 60000,

    coverageReporter: {
      dir: 'coverage',
      reporters: [
        // reporters not supporting the `file` property
        { type: 'lcovonly' },
        { type: 'html' },
        { type: 'text-summary' }
      ]
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity,

    // proxy settings for coverage
    proxies: {
      '/resource/': 'http://127.0.0.1:9999/source/resource/',
      '/gosa/': 'http://127.0.0.1:9999/test/resource/gosa/',
      '/source/resource/': 'http://127.0.0.1:9999/source/resource/',
      '/test/': 'http://127.0.0.1:9999/test/',
      '/script/': '/base/test/script/',
      '/component/': '/absolute' + path.resolve(__dirname, '../component') + "/",
      '/source/class/': '/base/source/class/',
      '/qooxdoo': '/absolute' + path.resolve(__dirname, '../qooxdoo') + "/"
    },

    // proxy settings without coverage (proxying resources, including PHP scripts to a PHP enabled webserver)
    // Note: you have to start a local php server with 'php -S 127.0.0.1:9999' in this folder
    //proxies: {
    //  '/resource/': 'http://127.0.0.1:9999/source/resource/',
    //  '/qx/': 'http://127.0.0.1:9999/test/resource/qx/',
    //  '/source/resource/': 'http://127.0.0.1:9999/source/resource/'
    //},

    qooxdooFramework: {
      testSources: true,  // test qooxdoo sources [default: false]
      startDelay: 0       // adds delay before the first test runs [default: 0], usefull if you want to open debugging tools in browser
                          // before running the tests
    }
  })
};
