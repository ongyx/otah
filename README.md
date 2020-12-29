# otah

otah generates OTA plist manifests for iOS `.ipa` apps.
This does **not** sign the `.ipa` file itself: the app must already be signed for it to be sucessfully installed.
(Unless you're jailbroken.)

## Usage
```
otah myapp.ipa -o manifest.plist -h mywebsite.com/path/to/ipa/file
```

## License
MIT.
