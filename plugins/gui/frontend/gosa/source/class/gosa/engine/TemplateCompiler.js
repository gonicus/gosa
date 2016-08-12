qx.Class.define("gosa.engine.TemplateCompiler", {
  type : "static",

  statics : {

    /**
     * Takes a json template as string and compiles it to a javascript object (includes translation etc.).
     *
     * @param template {String} The template as a json string
     * @return {Object} Compiled template
     */
    compile : function(template) {
      var translator = gosa.engine.Translator.getInstance();
      var translated = translator.translateJson(template);
      return JSON.parse(translated);
    }
  }
});
