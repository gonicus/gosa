qx.Class.define("gosa.test.data.TemplateRegistryTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testAddAndGetTemplates : function() {
      var registry = gosa.data.TemplateRegistry.getInstance();

      this.assertFunction(registry.addTemplate);

      this.assertNull(registry.getTemplates("foobar"));

      registry.addTemplate("myExtension", "template1", "{}");
      var templates = registry.getTemplates("myExtension");
      this.assertMap(templates);
      this.assertKeyInMap("template1", templates);
      this.assertObject(templates.template1);

      registry.addTemplate("myExtension", "template2", "{}");
      templates = registry.getTemplates("myExtension");
      this.assertMap(templates);
      this.assertKeyInMap("template1", templates);
      this.assertObject(templates.template1);
      this.assertKeyInMap("template2", templates);
      this.assertObject(templates.template2);
    },

    testAddMultipleTemplatesAtOnce : function() {
      var registry = gosa.data.TemplateRegistry.getInstance();

      registry.assertFunction(registry.addTemplates);
      registry.addTemplates("myMultipleExtension", {
        "template1" : "{}",
        "template2" : "{}"
      });
      templates = registry.getTemplates("myMultipleExtension");
      this.assertMap(templates);
      this.assertKeyInMap("template1", templates);
      this.assertObject(templates.template1);
      this.assertKeyInMap("template2", templates);
      this.assertObject(templates.template2);
    }
  }
});
