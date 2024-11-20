# 接口文档

## 显隐控制台指令
  
```
ps.emitMessage(
{
        "action": "controlpanel",
        "des": "显示控制台",
        "isOpen":true
        
    }
)
``
  isOpen    是否启用    "isOpen":true    必须为true  
      

## 孪生体高亮指令
```
ps.emitMessage(
    {
        "action": "HighLight",
        "des": "孪生体高亮选中",
        "twinId": "FDF6357C4705351BA51D9F9A22A38751",
        "time":"2837497239",
        "isOpen": true
    }
)
```
  
isOpen    是否启用    "isOpen": true    true，表示高亮； false，表示取消高亮；  


## 孪生体定位指令
  
```
ps.emitMessage(
{
        "action": "Focus",
        "des": "孪生体聚焦定位",
        "twinId": "孪生体id",
        "time":"2837497239",
        "isOpen":true
        
    }
)
```
"ext": {
            "cameraPitch":200,
            "cameraYaw":100,
            "cameraDefaultDis":0,
            "cameraMaxDis":0,
            "cameraMinDis":0,
            "centerOffsetX":0,
            "centerOffsetY":0,
            "centerOffsetZ":0
        }

  isOpen    是否启用    "isOpen":true    必须为true  
  cameraPitch    相机在垂直方向的仰角        
  cameraYaw    相机在水平方向的偏移角度        
  cameraDefaultDis    相机距离孪生体的默认距离        
  cameraMaxDis    相机距离孪生体的最远距离        
  cameraMinDis    相机距离孪生体的最近距离        
  centerOffsetX    孪生体中心点偏移量x        
  centerOffsetY    孪生体中心点偏移量t        
  centerOffsetZ    孪生体中心点偏移量z    

  
## 孪生体报警指令
isOpen:是否启用    
scale:报警光圈缩放大小 
colorA、colorR、colorG、colorB:颜色        
            
```
ps.emitMessage(
    {
        "action": "Alarm",
        "des": "孪生体报警",
        "twinId": "孪生体id",
        "time":"2837497239",
        "isOpen": true,
        "ext": {
            "centerOffsetX":0,
            "centerOffsetY":0,
            "centerOffsetZ":0,
            "scale":0.5,
            "colorA": 1,
            "colorR": 1,
            "colorG": 0,
            "colorB": 0
            }
        
    }
)
```
 

## 围栏生成指令
```
ps.emitMessage(
    {
        "action": "CreateFence",
        "des": "生成围栏",
        "time": "2837497239",
        "twinId": "孪生体id",
        "isOpen": true,
        "ext": {
            "style": "bar",
            "centerOffsetX":0,
            "centerOffsetY":0,
            "centerOffsetZ":0,
            "sizeX":300,
            "sizeY":200,
            "sizeZ":200
        }
    }
)
```
  isOpen    是否显示    
  style    样式   
  size    围栏大小        


## 漫游
```
ps.emitMessage(
    {
        "Action": "Roam",   
      "isOpen":true,
        "ext": {
        },
        "time": 123123
    }
)
```
  isOpen:
      漫游开关 
  
## 重置鸟瞰相机
```
ps.emitMessage(
    {
        "Action": "resetcamera",
    	"des": "重置鸟瞰相机到初始点位"	
    }
    
)
```
action：
     重置鸟瞰相机到初始点位  
     
## 获取构筑物信息
```
ps.emitMessage(
    {
        "Action": "Buildings",
    	"des": "返回所有构筑物名字和GUID"
    }
)
```
返回所有构筑物名字和GUID  


## 播放漫游方案
```
ps.emitMessage(

    {
        "Action": "startPlan",  
    	"des": "播放漫游方案",	
    	"isOpen":true,
        "ext": { 
    	"planname":"方案1"
    	},
        "time": 123123
    }
)
```
播放漫游方案  
  isOpen    播放还是停止
  ext    
      对应方案名称
      "planname":"方案名称"

## 设置相机参数
```
ps.emitMessage(

    {
        "Action": "setCameraInfo",   
      "isOpen": true,
        "ext": {
    	"位置": {
                "X": -2174.81201171875,
                "Y": 15646.9375,
                "Z": 133.17572021484375
            },
            "旋转": {
                "Pitch": -22.558679580688477,
                "Roll": 2.8659827876253985e-05,
                "Yaw": 120.40608978271484
            },
    		"zoom": 0,
            "duration":0.2
            
        },
        "time": 123123
    }
)
```
 设置相机  
  isOpen    模式开关
  ext    参数：相机位置信息 
         位置：相机位置 
         旋转：相机旋转 
         zoom：相机缩放 
         duration：过渡时间  
         
## 获取POI信息
```
ps.emitMessage(

    	{
        "action": "getpoi",
    	"des": "获取poi",
        "isOpen": true
    }
    
)
```
 获取POI点信息  

## 自定义POI聚焦
```
ps.emitMessage(

    {
        "action": "Focus_POI",
        "des": "自定义POI聚焦定位",
        "twinId": "孪生体id",
        "isOpen":true
    }
)
```
自定义POI聚焦定位  
  isOpen    是否启用   必须为true  
  twinId    自定义POIid     
            "twinId": "孪生体id"    
            程序内部定义：增加POI的视角  
       

## 时间膨胀（加速减速）
```
ps.emitMessage(

    	{
        "action": "TimeDilation",
    	"des": "速度调整",
        "isOpen": true,
        "ext":{
            "speed":5
              }
    
    }
    
)
```
速度调整  
  isOpen    模式开关    "isOpen":true,     
  ext    速度值 
         "speed":5
            5倍速  

## 暂停/开始
```
ps.emitMessage(

    	{
        "action": "SetPaused",
    	"des": "暂停",
        "isOpen": true
        
    
    }
)
```
速度调整  
  isOpen    模式开关
            "isOpen":true,
            暂停状态  

## 重置接口
```
ps.emitMessage(

     {
            "Action": "allreset",
            "des": "重置",
            "ext": {},
            "isOpen": true,
            "time": 123123
        }
)
```
 重置  
  isOpen    模式开关
           "isOpen":true,    
           


## 设置序列动画的
```
ps.emitMessage(

     {
            "action": "SetCurrentFrame",
            "des": "播放到序列动画的某一帧",
            "ext": {
                "frame": 8000
            },
            "isOpen": true
        }
)
```
序列动画 播放到某一帧  
  ext    帧数
         "ext":{
          "frame":8000 
          }pa


## 设置当前分辨率
```
ps.emitMessage(

    {
            "Action": "SetResolution",
            "des": "设置分辨率",
            "ext": {
    			"x":720,
    			"y":360
    		},
            "isOpen":true,
            "time": 123123
        }
)
```
设置分辨率  
  ext    x:分辨率x y:分辨率y 
        "ext": {    "x":720,   "y":360 }     
  isOpen       "isOpen":true,     

## 通过标签显隐
```
ps.emitMessage(

     {
            "action": "SetActorHiddenWithTag",
            "des": "通过标签显隐",
            "isOpen": true,
    		"ext":{
    		"tag":"电子围栏"  //“电子围栏”和“四色图”
    
    		
    		}
        }
)
```
通过标签显隐  
  isOpen    显隐开关        
  ext    tag 
         "tag":"电子围栏" 

## 天气控制
```
ps.emitMessage(

   {
        "Action": "Weather",
        "des": "天气控制",
		"isOpen": true,
        "ext": {
            "Type": "Rain_Thunderstorm"
        },
        "time": 123123,
        "zhushi": " Clear_Skies,Cloudy,Foggy,Overcast,Party_Cloudy,Rain,Rain_Light,Rain_Thunderstorm,Sand_Dust_Calm,Sand_Dust_Storm,Snow,Snow_Blizzard,Snow_Light"
    }
)
```
天气控制  
  isOpen    开关        
  ext    Type 对应天气类型
         "Type":
            Clear_Skies  晴
            Cloudy,Foggy 阴
            Overcast 阴
            Party_Cloudy 阴
            Rain 雨
            Rain_Light 雨
            Rain_Thunderstorm 雷
            Sand_Dust_Calm 沙
            Sand_Dust_Storm 沙
            Snow,Snow_Blizzard 雪
            Snow_Light 雪

## 时间控制
```
ps.emitMessage(

 {
        "Action": "time",
        "des": "时间控制",
        "ext": {
            "AnimateTimeOfDay": true,
            "DayLength": 1,
            "NightLength": 1,
            "time": "1200"
        },
        "time": 123123
    }
)
```
时间控制  
  isOpen    开关        
  ext    
    "AnimateTimeOfDay": true, 默认为true 自动更新时间
    "DayLength": 720, 默认为720       白天时间周期 720分钟12小时
    "NightLength": 720, 默认为720      黑夜时间 周期 720分钟12小时
    "time": "1200",  当前时间


 
## 序列动画播放
```
// 序列动画播放
ps.emitMessage(
    	{
        "action": "LevelSequencer",
    	"des": "播放序列",
        "isOpen": true,
    "ext":{
    "name":"SQ_整体",
    "bar":true
    },
        }
)
```
序列动画  
  isOpen    模式开关
  ext    参数：动画序列名字   
         "name":"test"            
         
## 管路显隐
```
// 管路显隐
ps.emitMessage(
    	{
        "action": "Pipeview",
    	"des": "管路显隐",
        "isOpen": true
        }
)
```
序列动画  
  isOpen    模式开关

## 加药间测试数据
```
// 加药间实时数据
ps.emitMessage(
    	{
    "Action": "updatebuildingtag",
    "ext": {

        "result": [{
                "metrics": [{
                        "metricName": "1#乙酸钠计量泵",
                        "metricUnit": "m3/h",
                        "nm": "1#乙酸钠计量泵",
                        "structGuid": "1834135888561692674",
                        "structName": "加药间",
                        "value": "2"
                    }, {
                        "metricName": "2#乙酸钠计量泵",
                        "metricUnit": "m³",
                        "nm": "2#乙酸钠计量泵",
                        "structGuid": "1834135888582664194",
                        "structName": "加药间",
                        "value": "0.1"
                    }, {
                        "metricName": "3#乙酸钠计量泵",
                        "metricUnit": "m³",
                        "nm": "3#乙酸钠计量泵",
                        "structGuid": "1834135888603635714",
                        "structName": "加药间",
                        "value": "0.2"
                    }, {
                        "metricName": "4#乙酸钠计量泵",
                        "metricUnit": "m³",
                        "nm": "LHTSBFJSZGLJPV",
                        "structGuid": "1834135888624607233",
                        "structName": "加药间",
                        "value": "0.3"
                    }, {
                        "metricName": "5#乙酸钠计量泵",
                        "metricUnit": "m³",
                        "nm": "LHTSBFJSZGLJPV",
                        "structGuid": "1834135888641384449",
                        "structName": "加药间",
                        "value": "0.4"
                    }, {
                        "metricName": "6#乙酸钠计量泵",
                        "metricUnit": "m³",
                        "nm": "LHTSBFJSZGLJPV",
                        "structGuid": "1834135888658161666",
                        "structName": "加药间",
                        "value": "0.5"
                    }
                ],
                "structGuid": "8",
                "structName": "加药间"
            }
        ],
        "success": true,
        "timestamp": 1698734651225
    },
    "isopen": true,
    "time": 123123
}

)
```
加药间实时数据更新（默认不显示，需要单独开启显示） 
  isOpen    模式开关
  
  
## 实时数据显示
```
// 所有实时数据显示
ps.emitMessage(
    	{
	"action": "RealData",
    "des": "实时数据显示",
	
	"isOpen": true
}
)
```
实时数据显示  
  isOpen    模式开关


## 单一实时数据显示
```
// 单一实时数据显示
ps.emitMessage(
    	{
	"action": "SingleRealData",
    "des": "单一实时数据显示",
	"ext":
	{
		"buildingName": "加药间"
	},
	
	"isOpen": false
}
)
```
单一实时数据显示  
  isOpen    模式开关



## 区域聚焦
```
// 区域聚焦
ps.emitMessage(
    	{
	"action": "Focus_Area",
    "des": "区域聚焦",
	"twinID":"CSBJArea",
	
	"isOpen": true
}
)
```
区域聚焦  
  isOpen    模式开关


## 液位同步
```
// 液位同步
ps.emitMessage(
    	{
    "action": "LiquidLevel",
    "des": "液位高度控制",
    "time": "1698734651225",
    "ext": {
        "GX2_1CSB_AI_OUT": 0.5
    }
}
)
```
液位高度控制  
ext:
    采集指标点列表对应0-1的液位高度




## 自动巡检
```
ps.emitMessage(

{
	"action": "Patrol",
	"des": "孪生体聚焦定位",
	"twinId": "E950227D45A9652D614750A51B6F5103",
	"time": "2837497239",
	"isOpen": true,
	"ext":
	{
		"模型名称": "小白人",
		"实例名称": "巡检测试人员",
		"计划名称": "巡检测试",
		"patrolPoins": [
			
			"S0001",
			"S0002",
			"S0003",
			"S0004"
		],
		"autoPatrol": true,
		"waitingTime": 5,
		"teleport_bool": false
	}
}
)

```
自动巡检  
  isOpen    开 关闭需要另一个接口启动        Patrol_Parameter中的status
  ext  
  "模型名称": "小白人", 使用哪个模型
  "实例名称": "巡检测试人员", 显示名称
  "计划名称": "巡检测试",   自定义计划名称
  "patrolPoins": []     巡检点列表
  "autoPatrol": true,   是否自动巡检
  "waitingTime": 5,   停留时间
  "teleport_bool": false    是否闪现

## 巡检参数
```
ps.emitMessage(


{
	"action": "Patrol_Parameter",
	"des": "孪生体聚焦定位",
	"twinId": "E950227D45A9652D614750A51B6F5103",
	"time": "2837497239",
	"isOpen": true,
	"ext":
	{
		"Name":"巡检测试人员",
		"Status":"end"
		
	}
}
)
```
自动巡检  
  isOpen    开 不需要关闭
  ext  
  "Name":"巡检测试人员", 要设置参数的实例名称 与上面接口对应
  "Status":"end" 巡检状态
   Status 可选值：  
        Config 绘制路线
        play  开始巡检
        next 下一个点
        last 上一个点
        end 结束

  
