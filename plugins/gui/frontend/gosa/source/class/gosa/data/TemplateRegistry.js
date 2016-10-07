/**
 * Global registry for templates and information they contain.
 */
qx.Class.define("gosa.data.TemplateRegistry", {
  type : "singleton",
  extend : qx.core.Object,

  construct : function() {
    this._registry = {};
  },

  members : {
    _registry : null,

    /**
     * Adds a template to the registry.
     *
     * @param extension {String} Name of the extension the template belongs to
     * @param templateName {String} Name of the template; will be overridden if it already exists
     * @param template {String} The unparsed template, must be valid json
     */
    addTemplate : function(extension, templateName, template) {
      qx.core.Assert.assertString(extension);
      qx.core.Assert.assertString(templateName);
      qx.core.Assert.assertString(template);

      if (!this._registry.hasOwnProperty(extension)) {
        this._registry[extension] = {};
      }
      this._registry[extension][templateName] = gosa.util.Template.compileTemplate(template);
    },

    /**
     * Addes several templates for an extension in one.
     *
     * @param extension {String} Name of the extension the templates belong to
     * @param templates {Map} A map with keys being the
     */
    addTemplates : function(extension, templates) {
      qx.core.Assert.assertString(extension);
      qx.core.Assert.assertMap(templates);

      for (var templateName in templates) {
        if (templates.hasOwnProperty(templateName)) {
          this.addTemplate(extension, templateName, templates[templateName]);
        }
      }
    },

    /**
     * Returns all known templates for a given extension name.
     *
     * @param extension {String}
     * @return {Map | null} Key is template name, value the parsed template; null if nothing registered
     */
    getTemplates : function(extension) {
      qx.core.Assert.assertString(extension);

      if (this._registry.hasOwnProperty(extension)) {
        return this._registry[extension];
      }
      return null;
    }
  },

  destruct : function() {
    this._registry = null;
  }
});
