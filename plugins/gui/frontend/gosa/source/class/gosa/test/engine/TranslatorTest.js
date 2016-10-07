qx.Class.define("gosa.test.engine.TranslatorTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testTranslateJson : function() {
      var trans = gosa.engine.Translator.getInstance();

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
