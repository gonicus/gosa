/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.theme.Appearance",
{
  extend : qx.theme.indigo.Appearance,

  appearances :
  {
    "mergeButton" : {
      style: function(states){
        var style = {};
        style['backgroundColor'] = null;
        style['icon'] = null;
        style['padding'] = 4;
        style['paddingLeft'] = 22;
        if(states['checked']){
          style['paddingLeft'] = 0;
          style['backgroundColor'] = '#EDEDED';
          style['icon'] = 'gosa/images/22/actions/dialog-ok-apply.png';
        }
        return(style);
      }
    },

    "tabview-page/button/label" :
    {
      alias : "label",

      style : function(states)
      {
        return {
          font: states.focused ? 'underline' : 'default'
        };
      }
    },


    "table" :
    {
      style : function(states)
      {
        if (states.invalid) {
          return({decorator: "border-invalid"});
        }else{
          return({decorator: null});
        }
      }
    },


    "SearchAid" : {},

    "SearchAid/legend" :
    {
      alias : "atom",

      style : function()
      {
        return {
          textColor : "#808080",
          padding : [5, 0, 0, 5],
          font: "bold"
        };
      }
    },

    "SearchAid/frame" :
    {
      style : function()
      {
        return {
          backgroundColor : "background",
          padding : [5, 0, 0, 5],
          margin: [10, 0, 0, 0],
          decorator  : null
        };
      }
    },

    "SearchAidButton-frame" :
    {
      alias : "atom",

      style : function(states)
      {
        var weight;
        if (states.pressed || states.abandoned || states.checked) {
          weight = "bold";
        } else {
          weight = "default";
        }

        return {
          textColor : "red",
          font: weight
        };
      }
    },

    "SearchAidButton" :
    {
      alias : "SearchAidButton-frame",
      include : "SearchAidButton-frame",

      style : function(states)
      {
        return {
          center : false,
          cursor: states.disabled ? undefined : "pointer"
        };
      }
    },

    "attribute-button-frame" :
    {
      alias : "atom",

      style : function(states)
      {
        var decorator;

        if (!states.disabled) {
          if (states.hovered && !states.pressed && !states.checked) {
            decorator = "button-box-hovered";
          } else if (states.hovered && (states.pressed || states.checked)) {
            decorator = "button-box-pressed-hovered";
          } else if (states.pressed || states.checked) {
            decorator = "button-box-pressed";
          }
        }

        return {
          decorator : decorator,
          padding : [3, 7],
          cursor: states.disabled ? undefined : "pointer",
          minWidth: 28,
          minHeight: 28
        };
      }
    },

    "attribute-button" : {
      alias : "attribute-button-frame",
      include : "attribute-button-frame",

      style : function(){
        return {
          center : true
        };
      }
    },

    "SearchList" :
    {
      alias : "scrollarea"
      //,include : "textfield"
    },

    "SearchListItem-Icon" :
    {
      style : function()
      {
        return {};
      }
    },

    "SearchLIstItem-Dn" :
    {
      style : function()
      {
        return {
          textColor : "green",
          cursor: "default"
        };
      }
    },

    "SearchLIstItem-Title" :
    {
      style : function()
      {
        return {
          textColor : "blue",
          cursor: "pointer",
          font : "SearchResultTitle"
        };
      }
    },

    "SearchLIstItem-Description" :
    {
      style : function()
      {
        return {
          textColor : "black"
        };
      }
    },


    "SearchListItem":
    {
      alias : "atom",

      style : function(states)
      {
        var padding = [3, 5, 3, 5];
        if (states.lead) {
          padding = [ 2, 4 , 2, 4];
        }
        if (states.dragover) {
          padding[2] -= 2;
        }

        var backgroundColor = states.hovered ? 'light-background' : undefined;

        return {
          padding : padding,
          backgroundColor : backgroundColor,
          textColor : states.selected ? "text-selected" : undefined,
          decorator : states.lead ? "lead-item" : states.dragover ? "dragover" : undefined
        };
      }
    },

    "title-bar":
    {
      alias : "atom",

      style : function()
      {
        return {
          backgroundColor : "#303030"
        };
      }
    },

    "statusLabel": {
      include: "label",

      style : function(states) {

        var tc = null;
        if (states.error) {
          tc = "error-text";
        }

        return {
          textColor: tc
        };
      }
    }

  }
});
