/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Controller for the {@link gosa.ui.widget.WorkflowWizard} widget; connects it to the model.
 */
qx.Class.define("gosa.data.WorkflowController", {

  extend : qx.core.Object,

  /**
   * @param obj {gosa.proxy.Object}
   * @param widget {gosa.ui.widgets.WorkflowWizard}
   */
  construct : function(obj, widget) {
    this.base(arguments);
    qx.core.Assert.assertInstance(obj, gosa.proxy.Object);
    qx.core.Assert.assertInstance(widget, gosa.ui.widgets.WorkflowWizard);
  }
});
