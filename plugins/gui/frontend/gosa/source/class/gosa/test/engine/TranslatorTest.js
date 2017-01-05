/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

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
