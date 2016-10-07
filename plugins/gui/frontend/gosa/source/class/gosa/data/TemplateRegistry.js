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
     * @param template {String} The unparsed template, must be valid json
     */
    addTemplate : function(extension, template) {
      qx.core.Assert.assertString(extension);
      qx.core.Assert.assertString(template);

      if (!this._registry.hasOwnProperty(extension)) {
        this._registry[extension] = [];
      }
      this._registry[extension].push(gosa.util.Template.compileTemplate(template));
    },

    /**
     * Addes several templates for an extension in one.
     *
     * @param extension {String} Name of the extension the templates belong to
     * @param templates {Array} A list of unparsed templates (strings that are valid json)
     */
    addTemplates : function(extension, templates) {
      qx.core.Assert.assertString(extension);
      qx.core.Assert.assertArray(templates);

      templates.forEach(function(template) {
        this.addTemplate(extension, template);
      }, this);
    },

    /**
     * Returns all known templates for a given extension name.
     *
     * @param extension {String} The extension to get the templates for
     * @return {Array} List of parsed template; empty if no templates are registered
     */
    getTemplates : function(extension) {
      qx.core.Assert.assertString(extension);

      if (this._registry.hasOwnProperty(extension)) {
        return this._registry[extension];
      }
      return [];
    }
  },

  destruct : function() {
    this._registry = null;
  }
});
