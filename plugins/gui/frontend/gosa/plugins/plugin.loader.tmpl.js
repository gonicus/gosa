(function(){

if (!window.qx) window.qx = {};

qx.$$start = new Date();

if (!qx.$$environment) qx.$$environment = {};
var envinfo = %{EnvSettings};
for (var k in envinfo) {
  // do not replace existing definitions
  if (!qx.$$environment[k]) {
    qx.$$environment[k] = envinfo[k];
  }
}
var package = envinfo['qx.application'].split(".");
package.pop();
package = package.join(".");
var baseDir = '../uploads/widgets/'+package+'/';

if (!qx.$$libraries) qx.$$libraries = {};
var libinfo = %{Libinfo};
for (var k in libinfo) {
  // do not replace existing definitions
  if (!qx.$$libraries[k]) {
    if (k === package) {
      qx.$$libraries[k] = {
        sourceUri: baseDir+libinfo[k].sourceUri,
        resourceUri: baseDir+libinfo[k].resourceUri
      };
    } else {
      qx.$$libraries[k] = libinfo[k];
    }
  }
}

if (!qx.$$resources) qx.$$resources = %{Resources};
if (!qx.$$translations) qx.$$translations = %{Translations};
if (!qx.$$locales) qx.$$locales = %{Locales};
if (!qx.$$packageData) qx.$$packageData = {};
if (!qx.$$g) qx.$$g = {};

qx.$$pluginLoader = {
  parts : %{Parts},
  packages : %{Packages},
  urisBefore : %{UrisBefore},
  cssBefore : %{CssBefore},
  boot : %{Boot},
  closureParts : %{ClosureParts},
  bootIsInline : %{BootIsInline},
  addNoCacheParam : %{NoCacheParam},
  delayDefer: false,

  decodeUris : function(compressedUris)
  {
    var libs = qx.$$libraries;
    var uris = [];
    for (var i=0; i<compressedUris.length; i++)
    {
      var uri = compressedUris[i].split(":");
      var euri;
      if (uri.length==2 && uri[0] in libs) {
        var prefix = libs[uri[0]].sourceUri;
        euri = prefix + "/" + uri[1];
      } else {
        euri = compressedUris[i];
      }
      if (qx.$$pluginLoader.addNoCacheParam) {
        euri += "?nocache=" + Math.random();
      }
      %{DecodeUrisPlug}
      uris.push(euri);
    }
    return uris;
  }
};

var readyStateValue = {"complete" : true};
if (document.documentMode && document.documentMode < 10 ||
    (typeof window.ActiveXObject !== "undefined" && !document.documentMode)) {
  readyStateValue["loaded"] = true;
}

function loadScript(uri, callback) {
  var elem = document.createElement("script");
  elem.charset = "utf-8";
  elem.src = uri;
  elem.onreadystatechange = elem.onload = function() {
    if (!this.readyState || readyStateValue[this.readyState]) {
      elem.onreadystatechange = elem.onload = null;
      if (typeof callback === "function") {
        callback();
      }
    }
  };

  if (isLoadParallel) {
    elem.async = null;
  }

  var head = document.getElementsByTagName("head")[0];
  head.appendChild(elem);
}

function loadCss(uri) {
  var elem = document.createElement("link");
  elem.rel = "stylesheet";
  elem.type= "text/css";
  elem.href= uri;
  var head = document.getElementsByTagName("head")[0];
  head.appendChild(elem);
}

var isWebkit = /AppleWebKit\/([^ ]+)/.test(navigator.userAgent);
var isLoadParallel = 'async' in document.createElement('script');

function loadScriptList(list, callback) {
  if (list.length == 0) {
    callback();
    return;
  }

  var item;

  if (isLoadParallel) {
    while (list.length) {
      item = list.shift();
      if (list.length) {
        loadScript(item);
      } else {
        loadScript(item, callback);
      }
    }
  } else {
    item = list.shift();
    loadScript(item,  function() {
      if (isWebkit) {
        // force async, else Safari fails with a "maximum recursion depth exceeded"
        window.setTimeout(function() {
          loadScriptList(list, callback);
        }, 0);
      } else {
        loadScriptList(list, callback);
      }
    });
  }
}

var fireContentLoadedEvent = function() {
  qx.$$domReady = true;
  document.removeEventListener('DOMContentLoaded', fireContentLoadedEvent, false);
};
if (document.addEventListener) {
  document.addEventListener('DOMContentLoaded', fireContentLoadedEvent, false);
}

qx.$$pluginLoader.importPackageData = function (dataMap, callback) {
  if (dataMap["resources"]){
    var resMap = dataMap["resources"];
    for (var k in resMap) {
      if (!qx.$$resources[k]) {
        qx.$$resources[k] = resMap[k];
      }
    }
  }
  var manager = qx.locale.Manager.getInstance();
  if (dataMap["locales"]){
    var locMap = dataMap["locales"];
    for (var lang in locMap){
      manager.addLocale(lang, locMap[lang]);
    }
  }
  if (dataMap["translations"]){
    var trMap   = dataMap["translations"];
    for (var lang in trMap){
      manager.addTranslation(lang, trMap[lang]);
    }
  }
  if (callback){
    callback(dataMap);
  }
}

qx.$$pluginLoader.signalStartup = function ()
{
  qx.Bootstrap.executePendingDefers();
  qx.$$pluginLoader.delayDefer = false;
  qx.$$pluginLoader.scriptLoaded = true;
  if (window.qx && qx.event && qx.event.handler && qx.event.handler.Application) {
    qx.event.handler.Application.onScriptLoaded();
    qx.$$pluginLoader.applicationHandlerReady = true;
  } else {
    qx.$$pluginLoader.applicationHandlerReady = false;
  }
}

// Load all stuff
qx.$$pluginLoader.init = function(){
  var l=qx.$$pluginLoader;
  if (l.cssBefore.length>0) {
    for (var i=0, m=l.cssBefore.length; i<m; i++) {
      loadCss(l.cssBefore[i]);
    }
  }
  if (l.urisBefore.length>0){
    loadScriptList(l.urisBefore, function(){
      l.initUris();
    });
  } else {
    l.initUris();
  }
}

// Load qooxdoo boot stuff
qx.$$pluginLoader.initUris = function(){
  var l=qx.$$pluginLoader;
  var bootPackageHash=l.parts[l.boot][0];
  if (l.bootIsInline){
    l.importPackageData(qx.$$packageData[bootPackageHash]);
    l.signalStartup();
  } else {
    loadScriptList(l.decodeUris(l.packages[l.parts[l.boot][0]].uris), function(){
      // Opera needs this extra time to parse the scripts
      window.setTimeout(function(){
        l.importPackageData(qx.$$packageData[bootPackageHash] || {});
        l.signalStartup();
      }, 0);
    });
  }
}
})();

%{BootPart}

qx.$$pluginLoader.init();

