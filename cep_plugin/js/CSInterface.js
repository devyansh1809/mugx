/*
CSInterface.js - Minimal version for basic CEP functionality
Download full version from: https://github.com/Adobe-CEP/CEP-Resources
*/

function CSInterface(){this.hostEnvironment=JSON.parse(window.__adobe_cep__.getHostEnvironment())}
CSInterface.prototype.evalScript=function(script,callback){var obj=this;window.__adobe_cep__.evalScript(script,function(result){if(callback){callback(result)}})};
CSInterface.prototype.getSystemPath=function(pathType){return window.__adobe_cep__.getSystemPath(pathType)};
CSInterface.prototype.openURLInDefaultBrowser=function(url){cep.util.openURLInDefaultBrowser(url)};
CSInterface.prototype.getExtensionID=function(){return this.hostEnvironment.extensionId};
CSInterface.prototype.getHostCapabilities=function(){return JSON.parse(window.__adobe_cep__.getHostCapabilities())};
CSInterface.prototype.dispatchEvent=function(event){window.__adobe_cep__.dispatchEvent(event)};
CSInterface.prototype.addEventListener=function(type,listener,obj){window.__adobe_cep__.addEventListener(type,listener,obj)};
CSInterface.prototype.removeEventListener=function(type,listener,obj){window.__adobe_cep__.removeEventListener(type,listener,obj)};
CSInterface.prototype.dumpPlaybackInfo=function(){window.__adobe_cep__.dumpPlaybackInfo()};
CSInterface.prototype.isResizeConstraintsChanged=function(){return JSON.parse(window.__adobe_cep__.isResizeConstraintsChanged())};
CSInterface.prototype.setPreference=function(key,value){window.__adobe_cep__.setPreference(key,value)};
CSInterface.prototype.getPreference=function(key){return window.__adobe_cep__.getPreference(key)};
CSInterface.prototype.deletePreference=function(key){window.__adobe_cep__.deletePreference(key)};
CSInterface.prototype.getPreferenceSync=function(key){return window.__adobe_cep__.getPreferenceSync(key)};
CSInterface.prototype.setPreferenceSync=function(key,value){window.__adobe_cep__.setPreferenceSync(key,value)};
CSInterface.prototype.deletePreferenceSync=function(key){window.__adobe_cep__.deletePreferenceSync(key)};
