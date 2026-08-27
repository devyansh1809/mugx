// SubliStudio CEP - Main ExtendScript Host
// This file imports all module functions
#target photoshop

// Document Operations (document_ops.jsx)
// Layer Operations (layer_ops.jsx)
// Smart Object Operations (smart_object_ops.jsx)
// Effects (effects.jsx)
// Export Operations (export_ops.jsx)

// Phase 0 functions (backward compatibility)
function getPhotoshopInfo(){try{var info={version:app.version,appName:app.name,hasDoc:false,docName:"",docWidth:0,docHeight:0,docResolution:0,colorMode:""};if(app.documents.length>0){var doc=app.activeDocument;info.hasDoc=true;info.docName=doc.name;info.docWidth=doc.width.as("cm");info.docHeight=doc.height.as("cm");info.docResolution=doc.resolution.as("px/in");switch(doc.mode){case DocumentMode.RGB:info.colorMode="RGB";break;case DocumentMode.CMYK:info.colorMode="CMYK";break;case DocumentMode.GRAYSCALE:info.colorMode="Grayscale";break;case DocumentMode.BITMAP:info.colorMode="Bitmap";break;case DocumentMode.LAB:info.colorMode="Lab";break;default:info.colorMode="Unknown"}}return JSON.stringify(info)}catch(e){return JSON.stringify({error:true,message:e.toString()})}}

function pingPhotoshop(){try{return JSON.stringify({success:true,version:app.version,message:"Photoshop is responding"})}catch(e){return JSON.stringify({success:false,error:e.toString()})}}

function createTestDocument(){try{var doc=app.documents.add(UnitValue(21,"cm"),UnitValue(29.7,"cm"),300,"SubliStudio Test",NewDocumentMode.RGB);return JSON.stringify({success:true,message:"Document created: "+doc.name,docName:doc.name})}catch(e){return JSON.stringify({success:false,error:e.toString()})}}

function log(message){$.writeln("[SubliStudio] "+message)}
