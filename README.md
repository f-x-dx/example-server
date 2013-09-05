example-server
==============

##Description
This is an application that provides an order ahead functionality, a loyalty program, and a custom tender type(paying by QR code). This is meant to be an example to show how to use the Clover APIs. The example itself uses Google App Engine for the server end of things, and also has an Android component. 

If you would like to try out the custom tender, you will also need to clone the example-android repository from here:

	https://github.com/clover/example-android

##Installation

####Git
If you haven't already, please install git from: 

	https://github.com/

####Cloning
Clone this repository to a directory of your choice. We will refer to the directory you cloned it to as <cloned_server_dir>.

If you would like to play with the Android side of things, you will also need to clone the Android repository, which you can find here:

	https://github.com/clover/example-android
	
We will refer to the Android repository directory as <cloned_android_dir>.

####Google App Engine
This project uses Google App Engine for Python, so if you don't have it you will need to install it. You can get it here: 

	https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python
	
We recommend you let it generate the symlinks when it asks since we will be using it here. 

####Python
In case it wasn't obvious from the Google App Engine section, this project uses Python. Specifically, this project was tested on Python 2.7. You can get it here:

	http://www.python.org/download/

####Creating the App on Clover
If you don't already have an account on http://stg1.dev.clover.com please create one. After you've made an account, create a developer account as well by clicking the drop down menu in the top right which says "Merchants" and then selecting "Create a New Developer". 

Now, click on "Create New App". You can name the app anything you would like, as long as the name is available. A checkmark will show if you hit check availability and the name is available. The same applies for the package name, which you will need if you want to also test the Android part of the app. Then hit "Create".

You should be on the Edit App page now. 

In the App Settings section, put in 

	http://localhost:8080
	
for the activation url. Also, put in

	localhost 
for the domain. Select both Read and Write for all options except Employees.

Hit Save Changes

You should be able to see the app and a debug version of it now in Your Apps. 

####Changing configuration of local server

Below "(No description yet)", you should be able to see the APP ID and App Secret on the "Your Apps" page. We will need to set your local server to use this APP ID and App Secret. 

Use your favorite text editor to open 

	<cloned_server_dir>/src/application/config.py
	
The first two lines should be assigning APP_SECRET and APP_ID. You should change that to assign to the APP ID and APP SECRET that you were given. 

####Publishing the app
Finally, let's actually publish the app! Click the Publish To My Merchants button on the right of the debug version of the app.  

If you are only planning on testing the web side, then under "Application type" select Web. Otherwise, select "Both". The Android side will not work without the web side so if you only want to check out the Android app you still have to set up the server. 

In Activation URL, put 

	http://localhost:8080/
	
If you selected "Both", then you will need the Android APK. If you haven't cloned the Android repository already, please do so now and then generate an APK. If you use Android Studio, you can do so by going to Build->Generate Signed APK.

And with all of that, you should finally be ready to start the server!

####Starting the server
First, let's go to the application directory at 

	<cloned_server_dir>/src
	
If this is your first time starting the server then you will need to run the generate_keys script. You can do so by entering

	python application/generate_keys.py

You may need to grant execute permissions first.

To actually start the server, enter

	dev_appserver.py --host=0.0.0.0 .

You can use the Google App Engine Launcher instead also, with directions at

	https://developers.google.com/appengine/docs/python/gettingstartedpython27/devenvironment

The reason you will need to set the host to "0.0.0.0" is to allow other devices on your network to be able to connect to the server, which is going to be required for the tablet device. 

Test that the server is working by going to 

	localhost:8080 
	
in your browser. 

####Linking a merchant
Before you can actually do anything with the app, you have to link merchants. Click "Merchant" at the very top of the web page go to the Merchant side of things. Then, click "Link Merchant" at the right. 

Select the merchant you want to link and you should be set!

You can try playing around on the web page now that you hvae a linked merchant, or if you want to try the Android code, you can continue to the Android setup section.

