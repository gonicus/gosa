/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Global registry for templates and information they contain.
 */
qx.Class.define("gosa.data.TemplateRegistry", {
  type : "singleton",
  extend : qx.core.Object,

  construct : function() {
    this._registry = {};
    this._dialogRegistry = {};
  },

  members : {
    _registry : null,
    _dialogRegistry : null,

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
    },

    /**
     * Checks if the given extension has at least one registered template.
     *
     * @param extension {String} Name of the extension
     * @return {Boolean}
     */
    hasTemplate : function(extension) {
      qx.core.Assert.assertString(extension);

      var value = this._registry[extension];
      return qx.lang.Type.isArray(value) && value.length > 0;
    },

    /**
     * Adds a dialog template to the registry. Existing keys will be overridden.
     *
     * @param templateName {String} Unique name of the template
     * @param template {String} The unparsed template as a valid json string
     */
    addDialogTemplate : function(templateName, template) {
      qx.core.Assert.assertString(templateName);
      qx.core.Assert.assertString(template);
      this._dialogRegistry[templateName] = gosa.util.Template.compileTemplate(template);
    },

    /**
     * Adds multiple dialog templates to the registry. Existing keys will be overridden.
     *
     * @param templateMap {Map} Hash map with keys being template names and the values the unparsed, valid json templates
     */
    addDialogTemplates : function(templateMap) {
      qx.core.Assert.assertMap(templateMap);

      for (var templateName in templateMap) {
        if (templateMap.hasOwnProperty(templateName)) {
          this.addDialogTemplate(templateName, templateMap[templateName]);
        }
      }
    },

    /**
     * Searches for a template by its name.
     *
     * @param templateName {String} Name by whiche the template was saved
     * @return {Object | null} The first found template or null if nothing found
     */
    getDialogTemplate : function(templateName) {
      qx.core.Assert.assertString(templateName);

      if (this._dialogRegistry.hasOwnProperty(templateName)) {
        return this._dialogRegistry[templateName];
      }
      return null;
    }
  },

  destruct : function() {
    this._registry = null;
    this._dialogRegistry = null;
  }
});
