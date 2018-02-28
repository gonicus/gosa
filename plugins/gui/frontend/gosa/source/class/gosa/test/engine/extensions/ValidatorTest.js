/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.test.engine.extensions.ValidatorTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    __extension : null,

    setUp : function() {
      this.__extension = new gosa.engine.extensions.Validator();
    },

    tearDown : function() {
      this.__extension.dispose();
      this.__extension = null;
    },

    _shouldValidate : function(form) {
      form.validate();
      this.assertTrue(form.getValidationManager().isValid());
    },

    _shouldNotValidate : function(form) {
      form.validate();
      this.assertFalse(form.getValidationManager().isValid());
    },

    testValidator5To120Letters : function() {
      var form = new qx.ui.form.Form();
      gosa.engine.SymbolTable.getInstance().addSymbol("form5To120LettersTest", form);
      var widget = new qx.ui.form.TextField();

      var data = {
        "name" : "5To120Letters",
        "form" : "@form5To120LettersTest"
      };
      this.__extension.process(data, widget);

      widget.setValue(null);
      this._shouldNotValidate(form);

      widget.setValue("");
      this._shouldNotValidate(form);

      widget.setValue("Abcd");
      this._shouldNotValidate(form);

      widget.setValue("Abcde");
      this._shouldValidate(form);

      var val = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
      widget.setValue(val);
      this._shouldValidate(form);

      val += "a";
      widget.setValue(val);
      this._shouldNotValidate(form);
    }
  }
});
