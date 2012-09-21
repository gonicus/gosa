/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

qx.Theme.define("cute.theme.Appearance",
{
  extend : qx.theme.indigo.Appearance,

  appearances :
  {

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

      style : function(states)
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
      style : function(states)
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
        var decorator = undefined;

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

      style : function(states){
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
      style : function(states)
      {
        return {};
      }
    },

    "SearchLIstItem-Dn" :
    {
      style : function(states)
      {
        return {
          textColor : "green",
          cursor: "default"
        };
      }
    },

    "SearchLIstItem-Title" :
    {
      style : function(states)
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
      style : function(states)
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
    }

  }
});
