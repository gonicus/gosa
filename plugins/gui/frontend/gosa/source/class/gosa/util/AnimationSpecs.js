/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Some specs which can be used for Animations
*/
qx.Class.define("gosa.util.AnimationSpecs", {
  type: "static",
  
  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    HIGHLIGHT_DROP_TARGET: {
      duration: 200,
      timing: "ease-in-out",
      keep: 100,
      keyFrames : {
        0: {
          scale : "1"
        },
        100: {
          scale : "1.2"
        }
      }
    },

    UNHIGHLIGHT_DROP_TARGET: {
      duration: 200,
      timing: "ease-in-out",
      keep: 100,
      keyFrames : {
        0: {
          scale : "1.2"
        },
        100: {
          scale : "1"
        }
      }
    },

    HIGHLIGHT_DROP_TARGET_BLINK: {
      duration: 400,
      timing: "ease-in-out",
      keep: 100,
      keyFrames : {
        0: {
          scale : "1"
        },
        50: {
          scale : "1.2"
        },
        100: {
          scale : "1"
        }
      }
    },

    SCALE_DRAGGED_ITEM: {
      duration: 100,
      timing: "ease-out",
      keep: 100,
      keyFrames : {
        0: {
          scale : "1"
        },
        100: {
          scale : "0.5"
        }
      }
    },

    UNSCALE_DRAGGED_ITEM: {
      duration: 100,
      timing: "ease-out",
      keep: 100,
      keyFrames : {
        0: {
          scale : "0.5"
        },
        100: {
          scale : "1.0"
        }
      }
    }
  }
});