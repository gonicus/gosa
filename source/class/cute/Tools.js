qx.Class.define("cute.Tools", {

  type: "static",

  statics: {

    createActionUrl: function(action, target){
      var url = document.location.origin + document.location.pathname;
      url += "#" + action + cute.Config.actionDelimiter + target;
      return(url);
    },

    getLocale: function(){
      if (cute.Config.locale) {
        var locale = cute.Config.locale;
      } else {
        var locale = qx.bom.client.Locale.getLocale();
        var variant = qx.bom.client.Locale.getVariant();
        if (locale && variant) {
          locale = locale + "-" + variant;
        }
      }
      return(locale);
    },

    serialize : function(queue)
    {
        var timer = qx.util.TimerManager.getInstance();
        var locked = false;

        timer.start(function(userData, timerId){
            if (locked) {
                return;
            } 

            locked = true;

            var entry = queue.shift();
            if (entry == undefined) {
                timer.stop();
                return;
            }

            var func = entry[0];
            var context = entry[1];
            var params = entry[2];
            params.push(function() {
                locked = false;
            });
            func.apply(context, params);
        }, 10, null, null, 0);
    }
  }
});
