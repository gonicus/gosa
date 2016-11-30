/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Loading indicator that shows a spinning refresh icon.
*/
qx.Class.define("gosa.ui.Throbber", {
  extend : qx.ui.basic.Atom,
  
  construct : function(icon) {
    this.base(arguments, null, icon || "@FontAwesome/spinner");

    this.addListener("appear", this.startAnimation, this);
    this.addListener("disappear", this.stopAnimation, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-spinner"
    },

    size: {
      check: "Number",
      init: 40,
      themeable: true,
      apply: "_applySize"
    }
  },
    
  members : {
    __handle: null,

    // property apply
    _applySize: function(value) {
      this.getChildControl("icon").set({
        width: value,
        height: value,
        scale: true
      });
    },

    /**
     * Start the spinner animation, this method is called automatically when the {gosa.zu.Throbber} receives the 'appear' event.
     */
    startAnimation: function() {
      if (!this.getBounds()) {
        this.addListenerOnce("appear", this.startAnimation, this);
        return;
      }
      if (!this.__handle || this.__handle.isEnded()) {
        this.__handle = qx.bom.element.Animation.animate(this.getContentElement().getDomElement(), {
          "duration"  : 500,
          "keep"      : 100,
          "keyFrames" : {
            0   : {"transform" : "rotate(0deg)"},
            100 : {"transform" : "rotate(359deg)"}
          },
          "origin"    : "50% 50%",
          "repeat"    : "infinite",
          "timing"    : "linear",
          "alternate" : false
        });
      } else {
        this.__handle.play();
      }
    },

    /**
     * Stop the spinner animation, this method is called automatically when the {gosa.zu.Throbber} receives the 'disppear' event.
     */
    stopAnimation: function() {
      if (this.__handle) {
        this.__handle.pause();
      }
    }

  }
});