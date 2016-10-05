qx.Class.define("gosa.test.engine.TranslatorTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    __instance : null,

    setUp : function() {
      this.__instance = new gosa.engine.Translator();
    },

    tearDown : function() {
      this.__instance.dispose();
      this.__instance = null;
    },

    testTranslateJson : function() {
      var trans = this.__instance;

      // no translation
      this.assertEquals("", trans.translateJson(""));
      this.assertEquals('{"foo": "bar"}', trans.translateJson('{"foo": "bar"}'));
      this.assertEquals('{"foo": "bar"}', trans.translateJson('{"foo": "tr(\'bar\')"}'));
      this.assertEquals('{"foo": "bar"}', trans.translateJson('{"foo": "trc(\'Something\', \'bar\')"}'));

      // simple translation
      var locManager = qx.locale.Manager.getInstance();
      locManager.addTranslation(locManager.getLocale(), {"bar": "baz"});
      this.assertEquals('{"foo": "baz"}', trans.translateJson('{"foo": "tr(\'bar\')"}'));
      this.assertEquals('{"foo": "baz"}', trans.translateJson('{"foo": "trc(\'Something\', \'bar\')"}'));
    }
  }
});
