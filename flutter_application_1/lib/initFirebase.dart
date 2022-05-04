// ignore_for_file: prefer_const_constructors

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_application_1/initUser.dart';
import 'package:firebase_core/firebase_core.dart';

class InitFirebase extends StatelessWidget {
  const InitFirebase({Key? key}) : super(key: key);

  Widget initApp(BuildContext context) {
    return FutureBuilder(
      future: Firebase.initializeApp(),
      builder: (BuildContext context, AsyncSnapshot snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: Text('Firebase load fail', textDirection: TextDirection.ltr),
          );
        }
        if (snapshot.connectionState == ConnectionState.done) {
          SystemChrome.setSystemUIOverlayStyle(
            SystemUiOverlayStyle.light.copyWith(
              statusBarColor: Colors.black, // Color for Android
              statusBarBrightness: Brightness.light, // for IOS.
            ),
          );
          return MaterialApp(
            home: InitUser(),
          );
        } else {
          return Center(
            child: CircularProgressIndicator(),
          );
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return initApp(context);
  }
}