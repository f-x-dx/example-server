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
If you don't already have an account on http://www.clover.com please create one. After you've made an account, create a developer account as well by clicking the drop down menu in the top right which says "Merchant" and then selecting "Create a New Developer". You can give your developer account any name you'd like.

Now, click on "Create New App" on the right. You can name the app anything you would like, as long as the name is available. A checkmark will show if you hit check availability and the name is available. 

The same applies for the package name, which you will need if you want to also test the Android part of the app. Note that you will need to rename the package name from within the Android application to match the name you give here. If you use Android Studio, you should be able to do this by going to the directory "com.clover.cloverexample" in Android Studio, right clicking, and then selecting Refactor->Rename and giving it a name of your choice. 

Make sure that the package name you give it and the one you set your app to be on the Clover website are the same and then hit "Create".

You should be on the Edit App page now. 

In the App Settings section, under activation url put 

	http://localhost:8080/clover_callback
	
Also, under domain put 

	localhost:8080
	 
Select both Read and Write for all options except Employees.

Hit Save Changes

You should be able to see the app and a debug version of it now in Your Apps. 

####Publishing the app
Finally, let's actually publish the app! Click the "Publish To My Merchants" button on the right of the debug version of the app.  
	
If you want to use the Android part of this application, then you will need to generate an APK and drag it into the box under "Upload Android APK". If you haven't cloned the Android repository already, please do so now and then generate an APK. If you use Android Studio, you can do so by going to Build->Generate Signed APK.

####Changing configuration of local server

Hopefully now your app is published! You will have to set up your local server to use the APP ID and App Secret given to your published app.

On the "Your Apps" page, for each of your apps, you should be able to see the APP ID and App Secret. We will need to set your local server to use the APP ID and App Secret of the debug version of your newly published app. 

Use your favorite text editor to open 

	<cloned_server_dir>/src/application/config.py
	
The first two lines should be assigning APP_SECRET and APP_ID. You should change that to assign to the APP ID and APP SECRET that you were given. For example, if your APP ID is "HPWE32KXQFZAM" and App Secret is "bbb3422c-1703-5049-cb9f-bfd3a6918937" then you would want your config.py file to have 

	APP_SECRET = "bbb3422c-1703-5049-cb9f-bfd3a6918937"
	APP_ID = "HPWE32KXQFZAM"

And with all of that, you should finally be ready to start the server!

####Starting the server
First, let's go to the application directory at 

	<cloned_server_dir>/src
	
If this is your first time starting the server then you will need to run the generate_keys script. You can do so with the command

	python application/generate_keys.py

To actually start the server, enter

	dev_appserver.py --host=0.0.0.0 .

You can use the Google App Engine Launcher instead also, with directions at

	https://developers.google.com/appengine/docs/python/gettingstartedpython27/devenvironment

The reason you will need to set the host to "0.0.0.0" is to allow other devices on your network to be able to connect to the server, which is going to be required for the tablet device. If you aren't planning on using the Android application, then you can leave the command out.

Test that the server is working by going to 

	localhost:8080 
	
in your browser. 

####Linking a merchant
Before you can actually do anything with the app, you have to link a merchant. On localhost:8080, click "Merchant" at the very top of the web page. Then, click "Link Merchant" at the right. 

Select the merchant you want to link(if you didn't make any extra ones there should only be one). Then, "Click Install App" and afterwards "Accept & Install".

If everything went smoothly, you should be back on the merchant home page with the merchant you linked showing. 

You can try playing around on the web page now that you hvae a linked merchant, or if you want to try the Android code, you can continue to the Android setup section.

####Android
If you are using a device registered under the same merchant that you installed the app for, then the app should have been installed automatically. You can check that the app was installed by going to "Apps" and clicking on it. If it was installed, there should be an option to open it.

However, the app relies on zxing's QR code scanner so you will need to install that for the example tender to work. You can download that from here:

	https://code.google.com/p/zxing/downloads/list
	
You want to download "BarcodeScanner". After downloading it, just use adb to install it with 

	adb install <apk file name>

That concludes the installation!

####Using the tender
To use the tender, just go to the "Register" app, and add something to your order then hit "Pay". A option named "Example Tender" should be there. You can change the name of this tender in 

<cloned_server_dir>/src/application/config.py

The QR code that you pay with can be found by going to 

	http://localhost:8080
	
and assuming you are on the customer home after signing in, clicking "Pay with My Code" on the right.
