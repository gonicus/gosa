/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Container showing several tabs - all necessary for displaying forms for editing an object.
 */
qx.Class.define("gosa.ui.widgets.WorkflowWizard", {

  extend: qx.ui.container.Composite,

  /**
   * @param templates {Array} List of hash maps in the shape {extension : <extension name>, template : <parsed template>}
   * @param asWorkflow {Boolean} use workflow mode: start with the first template and activate the next template once the last one is
   * filled with valid values
   */
  construct: function(templates) {
    this.base(arguments);
  },

  properties : {
    controller : {
      check : "gosa.data.controller.Workflow",
      init : null
    }
  }
});
