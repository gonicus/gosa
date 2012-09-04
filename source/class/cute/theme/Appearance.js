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
          center : false
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
          gap : 4,
          padding : padding,
          backgroundColor : backgroundColor,
          textColor : states.selected ? "text-selected" : undefined,
          decorator : states.lead ? "lead-item" : states.dragover ? "dragover" : undefined
        };
      }
    }

  }
});
