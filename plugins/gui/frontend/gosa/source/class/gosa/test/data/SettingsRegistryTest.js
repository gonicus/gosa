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

qx.Class.define("gosa.test.data.SettingsRegistryTest", {
  extend : qx.dev.unit.TestCase,
  include: qx.dev.unit.MMock,

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    testSetData : function() {
      gosa.data.SettingsRegistry.registerHandler(new gosa.data.settings.Handler("gosa.settings"));

      // check default editor
      var editor = gosa.data.SettingsRegistry.getEditor("gosa.settings");
      this.assertInstance(editor, gosa.ui.settings.Editor);
      this.assertEquals(editor.getNamespace(), "gosa.settings");

      // mock RPCs
      this.stub(gosa.io.Rpc.getInstance(), "cA");

      gosa.data.SettingsRegistry.set("gosa.settings.backend.index", false);
      this.assertFalse(gosa.data.SettingsRegistry.get("gosa.settings.backend.index"));

      // add listener
      gosa.data.SettingsRegistry.addListener("gosa.settings.backend.index", "change", function(value, old) {
        this.assertTrue(value);
        this.assertFalse(old);
      }, this);
      gosa.data.SettingsRegistry.set("gosa.settings.backend.index", true);
    }
  }
});
