qx.Class.define("gosa.util.Template", {
  type : "static",

  statics : {

    /**
     * Takes a json template as string and compiles it to a javascript object (includes translation etc.).
     *
     * @param template {String} The template as a json string
     * @return {Object} Compiled template
     */
    compileTemplate : function(template) {
      var translator = gosa.engine.Translator.getInstance();
      var translated = translator.translateJson(template);
      return JSON.parse(translated);
    },

    /**
     * Finds the gui templates for the given object name.
     *
     * @param objectName {String} The objectName (e.g. "PosixUser")
     * @param templates {Array | null} Array of all templates connected to the object name of null if nothing found
     */
    getTemplates : function(objectName) {
      if (!gosa.Cache.gui_templates.hasOwnProperty(objectName)) {
        qx.log.Logger.error("No template found for '" + objectName + "'.");
        return null;
      }
      return gosa.Cache.gui_templates[objectName];
    }
  }
});
