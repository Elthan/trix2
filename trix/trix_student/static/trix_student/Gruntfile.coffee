module.exports = (grunt) ->

  appfiles = {
    coffeecode: ['src/**/*.coffee', '!src/**/*.spec.coffee']
    scss: ['src/scss/*.scss', 'src/scss/**/*.scss']
  }

  vendorfiles = {
    fonts: [
      'node_modules/components-font-awesome/webfonts/fa-brands-400.eot'
      'node_modules/components-font-awesome/webfonts/fa-brands-400.svg'
      'node_modules/components-font-awesome/webfonts/fa-brands-400.ttf'
      'node_modules/components-font-awesome/webfonts/fa-brands-400.woff'
      'node_modules/components-font-awesome/webfonts/fa-brands-400.woff2'
      'node_modules/components-font-awesome/webfonts/fa-regular-400.eot'
      'node_modules/components-font-awesome/webfonts/fa-regular-400.svg'
      'node_modules/components-font-awesome/webfonts/fa-regular-400.ttf'
      'node_modules/components-font-awesome/webfonts/fa-regular-400.woff'
      'node_modules/components-font-awesome/webfonts/fa-regular-400.woff2'
      'node_modules/components-font-awesome/webfonts/fa-solid-900.eot'
      'node_modules/components-font-awesome/webfonts/fa-solid-900.svg'
      'node_modules/components-font-awesome/webfonts/fa-solid-900.ttf'
      'node_modules/components-font-awesome/webfonts/fa-solid-900.woff'
      'node_modules/components-font-awesome/webfonts/fa-solid-900.woff2'
    ]
    js: [
      'node_modules/angular/angular.min.js'
      'node_modules/angular/angular.min.js.map'
      'node_modules/angular-bootstrap/ui-bootstrap.min.js'
      'node_modules/angular-cookies/angular-cookies.min.js'
      'node_modules/angular-cookies/angular-cookies.min.js.map'
      'node_modules/angular-route/angular-route.min.js'
      'node_modules/angular-route/angular-route.min.js.map'
      'node_modules/bootstrap/dist/js/bootstrap.min.js'
      'node_modules/bootstrap/dist/js/bootstrap.min.js.map'
      'node_modules/jsurl/url.min.js'
      'node_modules/jquery/dist/jquery.min.js'
      'node_modules/jquery/dist/jquery.min.map'
      'node_modules/popper.js/dist/umd/popper.min.js'
      'node_modules/popper.js/dist/umd/popper.min.js.map'
    ]
  }

  grunt.loadNpmTasks('grunt-contrib-watch')
  grunt.loadNpmTasks('grunt-contrib-sass')
  grunt.loadNpmTasks('grunt-contrib-copy')
  grunt.loadNpmTasks('grunt-contrib-coffee')
  grunt.loadNpmTasks('grunt-coffeelint')
  grunt.loadNpmTasks('grunt-contrib-concat')
  grunt.loadNpmTasks('grunt-contrib-uglify')

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json')
    delta:
      sass:
        files: appfiles.scss
        tasks: 'sass'
      coffeecode:
        files: appfiles.coffeecode
        tasks: [
          'coffeelint:code', 'coffee:code', 'buildCodeDist']
      gruntfile:
        files: 'Gruntfile.coffee'
        tasks: ['coffeelint:gruntfile']

    sass:
      development:
        options:
          noSourceMap: true
          loadPath: ["scss", "node_modules"]
        files:
          ["dist/css/styles.css": "src/scss/styles.scss",
           "dist/css/wcag.css": "src/scss/wcag.scss"]

    coffeelint:
      code: appfiles.coffeecode
      gruntfile: ['Gruntfile.coffee']

    coffee:
      code:
        expand: true
        cwd: '.'
        src: appfiles.coffeecode
        dest: '.'
        ext: '.js'

    concat:
      trix_student:
        src: ['src/**/*.js', '!src/**/*.spec.js']
        dest: 'dist/js/trix_student.js'

    uglify:
      options:
        mangle: false
        sourceMap: true
      trix_student:
        files:
          'dist/js/trix_student.min.js': ['dist/js/trix_student.js']

    copy:
      vendor:
        files: [{
          expand: true
          flatten: true
          src: vendorfiles.fonts
          dest: 'dist/vendor/fonts/'
        }, {
          expand: true
          flatten: true
          src: vendorfiles.js
          dest: 'dist/vendor/js/'
        }]
  })

  grunt.registerTask('buildCodeDist', [
    'concat:trix_student'
    'uglify:trix_student'
  ])

  grunt.registerTask('build', [
    'coffeelint'
    'sass'
    'coffee:code'
    'buildCodeDist',
    'copy:vendor'
  ])

  grunt.registerTask('dist', [
    'build'
  ])

  # Rename the watch task to delta, and make a new watch task that runs
  # build on startup
  grunt.renameTask('watch', 'delta')
  grunt.registerTask('watch', [
    'build'
    'delta'
  ])

  grunt.registerTask('default', ['build'])
