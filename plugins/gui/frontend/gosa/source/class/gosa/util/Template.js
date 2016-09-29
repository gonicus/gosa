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
    },

    /**
     * Gives an array of maps with a template and other information.
     *
     * @param {String} The objectName (e.g. "PosixUser")
     * @param {String} The base type of the original object
     * @param {Array} An (maybe empty) array of hash maps
     */
    getTemplateObjects : function(objectName, baseType) {
      qx.core.Assert.assertString(objectName);
      qx.core.Assert.assertString(baseType);

      var self = gosa.util.Template;
      var result = [];

      self.getTemplates(objectName).forEach(function(template) {
        result.push({
          extension : objectName,
          isBaseType : objectName === baseType,
          template : self.compileTemplate(template)
        });
      });
      return result;
    },

    /**
     * Finds the identifying name of a dialog template.
     *
     * @param template {String} The template as a json string (i.e. unparsed)
     * @return {String | null} The name of the template or null if not found/no valid dialog template
     */
    getDialogName : function(template) {
      qx.core.Assert.assertString(template);
      var json = JSON.parse(template);
      if (json.hasOwnProperty("type") && json.type === "widget" &&
          json.hasOwnProperty("properties") && (typeof json.properties === "object") &&
          json.properties.hasOwnProperty("dialogName") && (typeof json.properties.dialogName === "string")) {
            return json.properties.dialogName;
          }
      return null;
    },

    /**
     * Finds the category title in the template.
     *
     * @param template {String} The unparsed template as a json string
     * @return {String | null} The category title or null if it does not exist/cannot be found
     */
    getCategoryTitle : function(template) {
      qx.core.Assert.assertString(template);
      var json = gosa.util.Template.compileTemplate(template);
      if (json.hasOwnProperty("type") && json.type === "widget" &&
          json.hasOwnProperty("properties") && (typeof json.properties === "object") &&
          json.properties.hasOwnProperty("categoryTitle") && (typeof json.properties.categoryTitle === "string")) {
            return json.properties.categoryTitle;
          }
      return null;
    }
  }
});
