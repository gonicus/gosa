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

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    testSetData : function() {
      var registry = gosa.data.SettingsRegistry.getInstance();

      // this.assertUndefined(registry.gosa.settings.index);
      registry.gosa.settings.index = false;
      this.assertFalse(registry.gosa.settings.index);

      // add listener
      gosa.data.SettingsRegistry.addListener("gosa.settings.index", "change", function(value, old) {
        this.assertTrue(value);
        this.assertFalse(old);
      }, this);
      registry.gosa.settings.index = true;
    }
  }
});
