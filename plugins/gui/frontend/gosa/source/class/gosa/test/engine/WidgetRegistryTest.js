/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Class.define("gosa.test.engine.WidgetRegistryTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    testAddAndGetWidget : function() {
      var registry = new gosa.engine.WidgetRegistry();

      // no entry
      this.assertUndefined(registry.getMap().foo);

      // one entry
      var widget = new qx.ui.basic.Label();
      registry.addWidget("foo", widget);
      this.assertEquals(widget, registry.getMap().foo);

      // removing all widgets
      registry.removeAndDisposeAllWidgets();
      this.assertUndefined(registry.getMap().foo);
    }
  }
});
