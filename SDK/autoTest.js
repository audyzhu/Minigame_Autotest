Laya.Stat.enable();
var isStartRecord = false;
var isStartReplay = false;
var isConnect = false;
var needSkip = false;
var intervalID;
var skipNum = 0;
var tcObjsCount = 0;
var tcObjsXpath = new Array();
var stepExeResult = {
  objNotActive: "objNotActive",
  objNotFound: "objNotFound",
  others: "otherError"
};
var actionSet = {
  click: Laya.Event.CLICK,
  move: Laya.Event.MOUSE_MOVE,
  type: Laya.Event.MOUSE_OVER

};
var xpathType = {
  customXY: 0 //待定
};

var mySocket;

var testDataFile = "autoTestCase.json";
var performDataFile = "perform.json";
var performData = new Array();
var maxTimes = 10;
var quickTime = 2000;
var oldTimeStamp = Date.parse(new Date());
(function setupUI() {
  var sp = new laya.display.Sprite();
  Laya.stage.addChild(sp);
  sp.name = "autoTestMenu";
  sp.zOrder = 99999;
  //画矩形
  sp.graphics.drawRect(400, 650, 400, 50, "#95A8B5");

  //录制按钮
  var btnStart = new Laya.Label();
  btnStart.name = "btnStart";
  btnStart.text = "开始录制";
  btnStart.fontSize = 24;
  btnStart.pos(400, 650);
  sp.addChild(btnStart);

  //回放按钮
  var btnReplay = new Laya.Label();
  btnReplay.name = "btnReplay";
  btnReplay.text = "开始回放";
  btnReplay.fontSize = 24;
  btnReplay.pos(500, 650);
  sp.addChild(btnReplay);

  //标记点
  var btnTip = new Laya.Label();
  btnTip.name = "btntip";
  btnTip.text = "标签开始";
  btnTip.fontSize = 24;
  btnTip.pos(700, 650);
  sp.addChild(btnTip);

  btnStart.on(Laya.Event.CLICK, this, () => {
    //let btnStartState = Laya.stage.getChildByName("autoTestMenu").getChildByName("btnStart") ;
    let btnReplayState = sp.getChildByName("btnReplay");

    if (btnStart.text == "开始录制" && btnReplayState.text == "开始回放") {//开始录制
      //开始录制标志位
      isStartRecord = true;
      btnStart.text = "结束录制";
      console.log("开始录制");
      //oldTimeStamp = Date.parse(new Date());
      oldTimeStamp = Date.now();
      //录制函数延迟执行
      setTimeout(recordingData, 500);

    }
    else if (btnStart.text == "开始录制" && btnReplayState.text == "结束回放") {
      console.log("正在回放中，请先结束回放后才能录制");
    }
    else if (btnStart.text == "结束录制") {
      isStartRecord = false;
      btnStart.text = "开始录制";
      //存储测试数据点
      saveData(testDataFile);
      console.log("结束录制");
    }
  });

  btnReplay.on(Laya.Event.CLICK, this, () => {
    let btnStartState = sp.getChildByName("btnStart");
    if (btnReplay.text == "开始回放" && btnStartState.text == "开始录制") {//开始回放
      //开始回放标志位
      isStartReplay = true;
      btnReplay.text = "结束回放";
      console.log("开始回放");
      resetPerformData(performDataFile);
      getPerform();
      //回放函数
      replayData();
    }
    else if (btnReplay.text == "开始回放" && btnStartState.text == "结束录制") {
      console.log("正在录制中，请先结束录制后才能回放");
    }
    else if (btnReplay.text == "结束回放") {
      isStartReplay = false;
      mySocket.send({ data: "end" });
      mySocket.close(mySocket);
      isConnect=false;
      clearInterval(intervalID);
      btnReplay.text = "开始回放";
      console.log("结束回放");
    }
  });

  btnTip.on(Laya.Event.CLICK, this, () => {
    let btnReplayState = sp.getChildByName("btnReplay");
    if (btnStart.text == "开始录制" && btnReplayState.text == "结束回放"&&btnTip.text=="标签开始") {
      btnTip.text = "标签结束"
      if (isConnect) {
        mySocket.send({ data: "tagStart" });
        console.log("tagStart");
      }
      console.log("标签开始");
    }
    else if (btnStart.text == "开始录制" && btnReplayState.text == "结束回放" && btnTip.text == "标签结束") {
      btnTip.text = "标签开始"
      if (isConnect) {
        mySocket.send({ data: "tagEnd" });
        console.log("tagEnd");
      }
      console.log("标签结束");
    }
    else if (btnTip.text == "标签开始") {
      btnTip.text = "标签结束"
      console.log("增加标签");
    }
    else if (btnTip.text == "标签结束") {
      btnTip.text = "标签开始"
      console.log("标签结束");
    }
    else if (btnStart.text == "开始录制" && btnReplayState.text == "开始回放") {
      console.log("请先开始录制或者回放");
    }
  });

})();


function getPerform() {
  let FPSSum = 0;
  let times = 0;
  mySocket = wx.connectSocket({
    url: 'ws://127.0.0.1:9001',
    header: {},
    method: '',
    protocols: [],
    success: function (res) { console.log(res) },
    fail: function (res) { console.log(res) },
    complete: function (res) { console.log(res) },
  });  
  mySocket.onError(function () { 
    console.error("connect perform server fail!");
    });
  mySocket.onOpen(function () {
    isConnect = true;
    let version = "1.0.1";
    beginMessage = "begin," + version;
    console.log(beginMessage)
    mySocket.send({ data: beginMessage });
    });  
  intervalID = setInterval(function () {
    let perform = {};
    perform.PFS = Laya.Stat.FPS;
    perform.mem = Math.round(Laya.Stat.currentMemorySize / 1000 / 10)/100 ;
    perform.dC = Laya.Stat.drawCall;
    perform.tri = Laya.Stat.trianglesFaces;
    performData[times] = perform;
    FPSSum += Laya.Stat.FPS;
    times++;
    if (times % 300 == 0) {
      console.log("avg FPS:" + FPSSum / 300);
      savePerform(performDataFile);
      times=0;
      FPSSum = 0;
    }
    console.log(perform);
    //FPS+mem+ drawCall+tri
    var message = perform.PFS + "," + perform.mem + "," + perform.dC + "," + perform.tri;
    if(isConnect){
      mySocket.send({ data: message });
    }
  }, 1000);
}

//存储测试数据函数
function saveData(testDataFile) {
  let testStr;
  testStr = JSON.stringify(tcObjsXpath);
  const fileSysManager = wx.getFileSystemManager();
  console.log("wx.env.USER_DATA_PATH=" + `${wx.env.USER_DATA_PATH}/` + testDataFile);
  fileSysManager.writeFileSync(`${wx.env.USER_DATA_PATH}/` + testDataFile, testStr, 'utf8');
}

function readData() {
  let testStr;
  let tcData = {};
  const fileSysManager = wx.getFileSystemManager();
  testStr = fileSysManager.readFileSync(`${wx.env.USER_DATA_PATH}/` + testDataFile, 'utf8');
  tcData = JSON.parse(testStr);
  console.log(tcData);
  return tcData;
}

//重置测试数据
function resetPerformData(performDataFile) {
  const fileSysManager = wx.getFileSystemManager();
  //console.log("wx.env.USER_DATA_PATH=" + `${wx.env.USER_DATA_PATH}/` + performDataFile);
  fileSysManager.writeFileSync(`${wx.env.USER_DATA_PATH}/` + performDataFile, "", 'utf8');
}

//存储测试数据
function savePerform(performDataFile) {
  let testStr;
  testStr = JSON.stringify(performData);
  const fileSysManager = wx.getFileSystemManager();

  console.log("wx.env.USER_DATA_PATH=" + `${wx.env.USER_DATA_PATH}/` + performDataFile);
  try {
    fileSysManager.appendFileSync(`${wx.env.USER_DATA_PATH}/` + performDataFile, testStr, 'utf8');
  } catch (err) {
    if (err.stack.toUpperCase().search("APPENDFILESYNC")>-1){
      fileSysManager.writeFileSync(`${wx.env.USER_DATA_PATH}/` + performDataFile, testStr, 'utf8');
    } else if (err.stack.toUpperCase().search("LIMIT") > -1){
      console.log("clear storage !");
      wx.clearStorageSync();
      fileSysManager.appendFileSync(`${wx.env.USER_DATA_PATH}/` + performDataFile, testStr, 'utf8');
    }
  }

}

//核心录制函数
function recordingData() {
  let oldEventDisplay = Laya.EventDispatcher.prototype.event;

  Laya.EventDispatcher.prototype.event = function (eventName, event) {
    if (eventName == "click" && isStartRecord) {
      event.stopPropagation();
      let stepNode = {};
      console.log("event.target.name = " + event.target.name);
      stepNode.xpath = getNodePath(event.target);
      stepNode.xpathType = 0;
      stepNode.action = "click";
      var newTimeStamp = Date.now();
      stepNode.sleepTime = newTimeStamp - oldTimeStamp;
      oldTimeStamp = newTimeStamp;
      tcObjsXpath[tcObjsCount] = stepNode;
      tcObjsCount++;
      console.log(stepNode);
    }
    oldEventDisplay.call(this, eventName, event);
  }


}

//存储结点相关节点路径
function getNodePath(target) {
  let num = 0;
  let xpath = new Array();
  while (target.parent != null) {
    let path = {};
    path.name = target.name;
    xpath[num++] = path;
    target = target.parent;
    console.log("path.name = " + path.name);
  }
  return xpath;
}

//用例回放
function replayData() {
  let testData = {};
  testData = readData(testDataFile);
  //console.log(tcObjsXpath);
  executeTest(testData);
}

//递归设置等待时间
function executeTestTime(testData, i, findTimes) {
  let findNodeTimes = findTimes;
  if (isStartReplay==false) return -1;
  if (i < testData.length) {
    if (needSkip) {
      needSkip = false;
      console.log("skip this node " + i + "success");
      executeTestTime(testData, i + 1, 0);
    } else {
      let waitTime = testData[i].sleepTime;
      if (findNodeTimes > 0) {
        waitTime = quickTime;
      }
      setTimeout(function () {
        let ret = executeStepNode(testData[i], findNodeTimes);
        if (ret == stepExeResult.stepExeOK) {
          console.log("execute step " + i + " successful");
          i++;
          findNodeTimes = 0;
          skipNum = 0;
          //doCheckPoint();
        } else if (findNodeTimes >= maxTimes) {
          console.error("execute step " + i + "fail");
          console.error(ret);
          if (skipNum < 2) {
            needSkip = true;
            skipNum++;
          } else {
            let btnReplayState = Laya.stage.getChildByName("autoTestMenu").getChildByName("btnReplay");
            btnReplayState.event("click");
            return -1;
          }

        } else {
          findNodeTimes++;
        }
        executeTestTime(testData, i, findNodeTimes);
      }, waitTime);
    }

  } else {
    let btnReplayState = Laya.stage.getChildByName("autoTestMenu").getChildByName("btnReplay");
    btnReplayState.event("click");
    return 1;
  }
}

function executeTest(testData) {
  let i = 0;
  let findNodeTimes = 0;
  executeTestTime(testData, 0, 0);
  return 1;

}

function executeStepNode(nodeXpath, findNodeTimes) {
  let nodeObj;
  let xpaths = nodeXpath.xpath;
  if (nodeXpath.xpathType == xpathType.customXY) {
    nodeObj = findNodeByXpath(xpaths, findNodeTimes);
  }
  else {
    console.error("exeStepNode: xpathType is " + nodeXpath.xpathType);
    return stepExeResult.others;
  }
  if (!nodeObj) {
    return stepExeResult.objNotFound;
  }
  if (nodeObj.activeInHierarchy == false) {
    return stepExeResult.objNotActive;
  }
  switch (nodeXpath.action) {
    case (actionSet.click):
      autoClick(nodeObj);
      break;
    case (actionSet.move):
      break;
    case (actionSet.type):
      break;
    default:
      break;
  }
  return stepExeResult.stepExeOK;
}


function findNodeByXpath(xpaths, findNodeTimes) {
  let targetNode;
  try {
    for (let i = xpaths.length - 1; i >= 0; i--) {
      if (i == xpaths.length - 1) {//根节点，结点倒叙存储

        targetNode = Laya.stage.getChildByName(xpaths[i].name);//Laya.Scene
        if (null == targetNode || "" == xpaths[i].name) {
          let j = 0;
          for (j = Laya.stage.numChildren - 1; j >= 0; j--) {
            console.log(Laya.stage._children[j].name);
            if (Laya.stage._children[j].name == xpaths[i].name) {
              targetNode = Laya.stage._children[j];
              console.log("find first name by step xpaths[i].name=" + xpaths[i].name);
              break;
            }
          }
          if (j < 0) {
            console.error("first target name  is (" + xpaths[i].name + ")");
            console.error("first current name  is (" + tempNode.name + ")");
            return null;
          }
        }
        //console.log("first xpaths[i].name=" + xpaths[i].name);
      } else {
        console.log("xpaths[" + i + "].name=" + xpaths[i].name);
        let tempNode = targetNode.getChildByName(xpaths[i].name);
        if (null == tempNode || "" == xpaths[i].name) {
          console.log("findNodeTimes is" + findNodeTimes + "targetNode.numChildren is " + targetNode.numChildren);
          //console.log("GUID is " + targetNode.$_GID);
          let j = 0;
          for (j = findNodeTimes; j < targetNode.numChildren; j++) {
            console.log(targetNode._children[j].name);
            if (targetNode._children[j].name == xpaths[i].name) {
              tempNode = targetNode._children[j];
              console.log("find name by step xpaths[i].name=" + xpaths[i].name);
              console.log("find name by step targetNode.name=" + tempNode.name);
              break;
            }
          }
          if (j >= targetNode.numChildren) {
            console.error("target name  is (" + xpaths[i].name + ")");
            console.error("current name  is (" + tempNode.name + ")");
            return null;
          }
        }
        targetNode = tempNode;//注释方便
        console.log("target.name = " + targetNode.name);
      }
    }
  } catch (err) {
    targetNode = null;
    console.error(err);
  }
  return targetNode;
}

//模仿点击
function autoClick(nodeObj) {
  if (null == nodeObj) {
    return 0;
  } else {
    try {
      console.log("event click:" + nodeObj.name);
      nodeObj.event("click", { type: "click" });
    } catch (err) {
      //var error1=new Error("hello");
      console.log(err.stack);
    }
  }
  return 1;
}


