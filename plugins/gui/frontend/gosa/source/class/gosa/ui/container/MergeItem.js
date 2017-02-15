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

qx.Class.define("gosa.ui.container.MergeItem", {
	extend: qx.ui.form.ToggleButton,

	construct: function(widget){
		this.base(arguments);
		this._setLayout(new qx.ui.layout.HBox(10));
		this._add(widget, {flex: 1});

		this.getChildControl("icon").setAlignY("middle");
	},

  properties : {
	  //overridden
		appearance : {
			refine : true,
			init : "merge-button"
    }
  },

	members : {
		// overridden
    /**
     * @lint ignoreReferenceField(_forwardStates)
     */
    _forwardStates :
    {
      checked : true
    }
	}
});
