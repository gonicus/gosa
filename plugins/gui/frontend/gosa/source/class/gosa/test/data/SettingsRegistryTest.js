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
      gosa.data.SettingsRegistry.registerHandler(new gosa.data.settings.ConfigHandler("gosa.settings"));

      // mock RPCs
      this.sinon.stub(gosa.io.Rpc.getInstance(), "cA");

      gosa.data.SettingsRegistry.set("gosa.settings.index", false);
      this.assertFalse(gosa.data.SettingsRegistry.get("gosa.settings.index"));

      // add listener
      gosa.data.SettingsRegistry.addListener("gosa.settings.index", "change", function(value, old) {
        this.assertTrue(value);
        this.assertFalse(old);
      }, this);
      gosa.data.SettingsRegistry.set("gosa.settings.index", true);
    }
  }
});
