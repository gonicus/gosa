/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.test.engine.ExtensionManagerTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testRegisterAndHandleExtension : function() {
      var manager = gosa.engine.ExtensionManager.getInstance();
      manager.registerExtension("foo", gosa.test.engine.SampleExtension);

      this.assertException(function() {manager.registerExtension("foo", gosa.test.engine.SampleExtension);});

      manager.handleExtension("foo", "bar", manager);
    }
  }
});
