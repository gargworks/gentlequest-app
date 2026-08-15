'use strict';
const MANIFEST = 'flutter-app-manifest';
const TEMP = 'flutter-temp-cache';
const CACHE_NAME = 'flutter-app-cache';

const RESOURCES = {"flutter_bootstrap.js": "3be31d65d314448e278213e366830672",
"version.json": "06413763c5232ff601a7b3f3bb6ed7f1",
"index.html": "52a1dc75875ad96b3f2da36096d63a03",
"/": "52a1dc75875ad96b3f2da36096d63a03",
"main.dart.js": "79590b0a7046e6d1af58137a6b41c9a7",
"flutter.js": "83d881c1dbb6d6bcd6b42e274605b69c",
"favicon.png": "713fc25890616a8feade94feb8335357",
"icons/Icon-192.png": "6d5a6c62c613a5a08802ab4cac849fa9",
"icons/Icon-maskable-192.png": "6d5a6c62c613a5a08802ab4cac849fa9",
"icons/Icon-maskable-512.png": "3010f6820d5582ed91fa3cae4f2d10a8",
"icons/Icon-512.png": "3010f6820d5582ed91fa3cae4f2d10a8",
"manifest.json": "9c8c22becdd15c50a59298d75c90f7e0",
"assets/AssetManifest.json": "6b96884633b01d0cabb1143f720db56a",
"assets/NOTICES": "16a045c5c6f2ffc7afc236834de3d085",
"assets/FontManifest.json": "73b0f74d5db464a27841772ff41e4c07",
"assets/AssetManifest.bin.json": "a4646540842cfe854b0a920bafa6a71b",
"assets/packages/cupertino_icons/assets/CupertinoIcons.ttf": "33b7d9392238c04c131b6ce224e13711",
"assets/shaders/ink_sparkle.frag": "ecc85a2e95f5e9f53123dcaf8cb9b6ce",
"assets/AssetManifest.bin": "a258fcc194ef4b58c47d878af84552c2",
"assets/fonts/MaterialIcons-Regular.otf": "65bbdcafcdf82d659e7566d18e73cfa1",
"assets/assets/images/quests/resource_music.svg": "fd7a7b8395fd3f3b647c78863d91b3f3",
"assets/assets/images/quests/task_focus.svg": "fc442ab2c3f2eee6ad69cb72b8f9b97b",
"assets/assets/images/quests/resource_headphone_match_v8_done.svg": "966a7ac5be6f64f6724f94a14bb7102c",
"assets/assets/images/quests/img_image_65x52.png": "c87748532a7ac9177fa05852d5edb745",
"assets/assets/images/quests/img.svg": "6c6f1a638cc9d6d32fd98c88fd9feedb",
"assets/assets/images/quests/img_image_43x43.png": "7f5741454acddbfb3360402379b53b27",
"assets/assets/images/quests/img_vector_0_gray_600_02.svg": "cfd68267af604f398ef8118fbe1679d2",
"assets/assets/images/quests/img_vector_0.svg": "63a0126acce5a6a5ed610c68f7d961a4",
"assets/assets/images/quests/resource_music_match_backup.svg": "292b8fea6e9486d399b9551ecd5174ba",
"assets/assets/images/quests/resource_headphone_match_v8.svg": "1216b4f58140cc6bbd8a6b32d2fc6041",
"assets/assets/images/quests/img_image_51x52.png": "fc009652c611893e3ccab90499254e19",
"assets/assets/images/quests/img_background_10x635.png": "58c9e81b4545dce1766277e21d3f1362",
"assets/assets/images/quests/img_background_1440x635_1.png": "ae3519e7c99c589b31a363b585469159",
"assets/assets/images/quests/img_vector_0_39x39.svg": "296b4182791278dda8745fe0fb5876ca",
"assets/assets/images/quests/task_study_done.svg": "c625b4557fd93a2e9206b833dfc7b1f4",
"assets/assets/images/quests/tip_generic.svg": "992822a363e5c2c233ce6f8d7a69d6ff",
"assets/assets/images/quests/task_study.svg": "0baca38087ff48d04203823cffbd46e2",
"assets/assets/images/quests/task_focus_done.svg": "92fc8bc5ffc43f78356500a7fff5d995",
"assets/assets/images/quests/img_background_104x521.png": "894c751780c3169270a99051c30651d0",
"assets/assets/images/quests/resource_music_note_c.svg": "3a2f2b23323480ed4f59beb8d6475437",
"assets/assets/images/quests/resource_music_match.svg": "bbd8e75bbf6836d10c0cc552d4e18de8",
"assets/assets/images/quests/img_background_13x635.png": "0e8864293c2b56e69b885d9e4a1f771e",
"assets/assets/images/quests/resource_generic.svg": "6e3399b63cfb794060794ad27a49eddd",
"assets/assets/images/quests/img_background_77x511.png": "8c75214695595cde0eba8d0ae946e33a",
"assets/assets/images/quests/img_image_66x66.png": "8a522d7b3f3835ef6883afbfa0c74451",
"assets/assets/images/quests/img_vector_0_gray_900.svg": "3381ecf25c3d9eeebecfa9a5a6341064",
"assets/assets/images/quests/img_image_32x32.png": "9db2727ae70f723b85f05fafb513d4dd",
"assets/assets/images/quests/img_image_52x52.png": "ee8c3421a2fac1a4ec037c51606b27c4",
"assets/assets/images/quests/img_image_47x72.png": "2bd5a10efe7cefb5131cc1f2a92fc006",
"assets/assets/images/quests/resource_music_match_v5.svg": "fb426e47f96c15457ae42b9e99bb2db4",
"assets/assets/images/quests/img_image_63x65.png": "61956d6f229b6d99ecebcaef3d6749f0",
"assets/assets/images/quests/img_image_131x130.png": "309cfceff0dccceca758775fa6857ed6",
"assets/assets/images/quests/resource_music_match_v4.svg": "e1f311c4903fda6d96f83d2714ed4c8c",
"assets/assets/images/quests/img_background_1440x635.png": "f8882284f3e4c52c0b7af9575e3d97c6",
"assets/assets/images/quests/img_image_130x130.png": "9aef857a69d7abe5e09bd5cd91d67458",
"assets/assets/images/quests/resource_music_match_v3.svg": "ab75b7f03f12d1cd6c64956c11ddb4e3",
"assets/assets/images/quests/resource_music_match_v2.svg": "c88a305ef4f01e818bcb5834cb5c8688",
"assets/assets/images/quests/img_vector_0_gray_600_02_1.svg": "fb2205c61ea9dd9288fa410f269538d9",
"assets/assets/images/quests/resource_headphone_match_v6.svg": "02b38048b7dcbdc4e57998ef2da50215",
"assets/assets/images/quests/resource_headphone_match_v7.svg": "61de5522ec129cfd1985b14435568ce1",
"assets/assets/images/quests/img_background_15x635.png": "35a3114c8a4c4d71ca33dc46841e4ea6",
"assets/assets/images/quests/img_image_1.png": "51ca0e93afac97e6a470a311fdf2dc52",
"assets/assets/images/quests/image_not_found.png": "a88029aaad6e6ea7596096c7c451840b",
"assets/assets/images/quests/tip_generic_done.svg": "2c6b6424a6bbb39d0da9a3e3239f3cb3",
"assets/assets/images/quests/resource_music_alt2.svg": "f907e5a7568d6b392b692b0c308e94a4",
"assets/assets/images/quests/img_image.png": "7143940b4e7c03760fccdcff0c706602",
"assets/assets/images/quests/img_background.png": "3685a652109d3f180f1c4844e107fb5d",
"assets/assets/images/quests/img_vector_0_gray_600_02_39x39.svg": "7210ca93f88e2fcdcb6510178c2baf6e",
"assets/assets/images/quests/img_image_38x38.png": "6b278687f2ffce0b0db1adf92aa46dcd",
"assets/assets/images/quests/resource_music_alt1.svg": "b65b8a9e2723a8c1e53abb8b86a91d7b",
"assets/assets/images/avatar_placeholder.png": "4d5bbf3e52203e7f5f1774e3b7ae71dd",
"assets/assets/images/img_image_65x52.png": "c87748532a7ac9177fa05852d5edb745",
"assets/assets/images/img.svg": "6c6f1a638cc9d6d32fd98c88fd9feedb",
"assets/assets/images/img_image_43x43.png": "7f5741454acddbfb3360402379b53b27",
"assets/assets/images/dhiwise/img_image_65x52.png": "c87748532a7ac9177fa05852d5edb745",
"assets/assets/images/dhiwise/img.svg": "6c6f1a638cc9d6d32fd98c88fd9feedb",
"assets/assets/images/dhiwise/img_image_43x43.png": "7f5741454acddbfb3360402379b53b27",
"assets/assets/images/dhiwise/img_vector_0_gray_600_02.svg": "cfd68267af604f398ef8118fbe1679d2",
"assets/assets/images/dhiwise/img_vector_0.svg": "63a0126acce5a6a5ed610c68f7d961a4",
"assets/assets/images/dhiwise/img_image_51x52.png": "fc009652c611893e3ccab90499254e19",
"assets/assets/images/dhiwise/img_background_10x635.png": "58c9e81b4545dce1766277e21d3f1362",
"assets/assets/images/dhiwise/img_background_1440x635_1.png": "ae3519e7c99c589b31a363b585469159",
"assets/assets/images/dhiwise/img_vector_0_39x39.svg": "296b4182791278dda8745fe0fb5876ca",
"assets/assets/images/dhiwise/img_background_104x521.png": "894c751780c3169270a99051c30651d0",
"assets/assets/images/dhiwise/img_background_13x635.png": "0e8864293c2b56e69b885d9e4a1f771e",
"assets/assets/images/dhiwise/img_background_77x511.png": "8c75214695595cde0eba8d0ae946e33a",
"assets/assets/images/dhiwise/img_image_66x66.png": "8a522d7b3f3835ef6883afbfa0c74451",
"assets/assets/images/dhiwise/img_vector_0_gray_900.svg": "3381ecf25c3d9eeebecfa9a5a6341064",
"assets/assets/images/dhiwise/img_image_32x32.png": "9db2727ae70f723b85f05fafb513d4dd",
"assets/assets/images/dhiwise/img_image_52x52.png": "ee8c3421a2fac1a4ec037c51606b27c4",
"assets/assets/images/dhiwise/img_image_47x72.png": "2bd5a10efe7cefb5131cc1f2a92fc006",
"assets/assets/images/dhiwise/img_image_63x65.png": "61956d6f229b6d99ecebcaef3d6749f0",
"assets/assets/images/dhiwise/img_image_131x130.png": "309cfceff0dccceca758775fa6857ed6",
"assets/assets/images/dhiwise/img_background_1440x635.png": "f8882284f3e4c52c0b7af9575e3d97c6",
"assets/assets/images/dhiwise/img_image_130x130.png": "9aef857a69d7abe5e09bd5cd91d67458",
"assets/assets/images/dhiwise/img_vector_0_gray_600_02_1.svg": "fb2205c61ea9dd9288fa410f269538d9",
"assets/assets/images/dhiwise/img_background_15x635.png": "35a3114c8a4c4d71ca33dc46841e4ea6",
"assets/assets/images/dhiwise/img_image_1.png": "51ca0e93afac97e6a470a311fdf2dc52",
"assets/assets/images/dhiwise/image_not_found.png": "a88029aaad6e6ea7596096c7c451840b",
"assets/assets/images/dhiwise/img_image.png": "7143940b4e7c03760fccdcff0c706602",
"assets/assets/images/dhiwise/img_background.png": "3685a652109d3f180f1c4844e107fb5d",
"assets/assets/images/dhiwise/img_vector_0_gray_600_02_39x39.svg": "7210ca93f88e2fcdcb6510178c2baf6e",
"assets/assets/images/dhiwise/img_image_38x38.png": "6b278687f2ffce0b0db1adf92aa46dcd",
"assets/assets/images/img_vector_0_gray_600_02.svg": "cfd68267af604f398ef8118fbe1679d2",
"assets/assets/images/img_vector_0.svg": "63a0126acce5a6a5ed610c68f7d961a4",
"assets/assets/images/img_image_51x52.png": "fc009652c611893e3ccab90499254e19",
"assets/assets/images/avatar_alex.png": "14c79ea44695be384d88bf32f01327ea",
"assets/assets/images/img_background_10x635.png": "58c9e81b4545dce1766277e21d3f1362",
"assets/assets/images/img_background_1440x635_1.png": "ae3519e7c99c589b31a363b585469159",
"assets/assets/images/img_vector_0_39x39.svg": "296b4182791278dda8745fe0fb5876ca",
"assets/assets/images/img_background_104x521.png": "894c751780c3169270a99051c30651d0",
"assets/assets/images/background_placeholder.png": "b0d0260a5d6613b63ca49cc9ae8091f0",
"assets/assets/images/img_background_13x635.png": "0e8864293c2b56e69b885d9e4a1f771e",
"assets/assets/images/img_background_77x511.png": "8c75214695595cde0eba8d0ae946e33a",
"assets/assets/images/img_image_66x66.png": "8a522d7b3f3835ef6883afbfa0c74451",
"assets/assets/images/img_vector_0_gray_900.svg": "3381ecf25c3d9eeebecfa9a5a6341064",
"assets/assets/images/img_image_32x32.png": "9db2727ae70f723b85f05fafb513d4dd",
"assets/assets/images/img_image_52x52.png": "ee8c3421a2fac1a4ec037c51606b27c4",
"assets/assets/images/img_image_47x72.png": "2bd5a10efe7cefb5131cc1f2a92fc006",
"assets/assets/images/img_image_63x65.png": "61956d6f229b6d99ecebcaef3d6749f0",
"assets/assets/images/img_image_131x130.png": "309cfceff0dccceca758775fa6857ed6",
"assets/assets/images/img_background_1440x635.png": "f8882284f3e4c52c0b7af9575e3d97c6",
"assets/assets/images/img_image_130x130.png": "9aef857a69d7abe5e09bd5cd91d67458",
"assets/assets/images/img_vector_0_gray_600_02_1.svg": "fb2205c61ea9dd9288fa410f269538d9",
"assets/assets/images/img_background_15x635.png": "35a3114c8a4c4d71ca33dc46841e4ea6",
"assets/assets/images/img_image_1.png": "51ca0e93afac97e6a470a311fdf2dc52",
"assets/assets/images/image_not_found.png": "a88029aaad6e6ea7596096c7c451840b",
"assets/assets/images/img_image.png": "7143940b4e7c03760fccdcff0c706602",
"assets/assets/images/img_background.png": "3685a652109d3f180f1c4844e107fb5d",
"assets/assets/images/reference/Unknown-5.png": "11b7e4c83395e39f67577e0f8ff1ebe6",
"assets/assets/images/reference/Unknown-4.png": "f90d487ea4924013209762ea03ccfaca",
"assets/assets/images/reference/WelcomeScreen.png": "b0d0260a5d6613b63ca49cc9ae8091f0",
"assets/assets/images/reference/Unknown-6.png": "6ccb21622a995fd6e2f71c32b819fda1",
"assets/assets/images/reference/Unknown-12(1).png": "bdda30f1f63c5717f952927752499efc",
"assets/assets/images/reference/Unknown-7.png": "18c6539e5d618e0d1cc4c27c9e175c68",
"assets/assets/images/reference/Unknown-3.png": "cc3912f09364252cae477882496a4b74",
"assets/assets/images/reference/Unknown-26(635%2520x%25201440%2520px).png": "79a8bdb226e6906d1235f0184b12a09b",
"assets/assets/images/reference/Unknown-13.png": "ea0fa69600216c4f4e796a56c863970f",
"assets/assets/images/reference/Unknown-26(635%2520x%25201440%2520px).svg": "fc3216033c6249e4789536ffc484b3d2",
"assets/assets/images/reference/Unknown-11.png": "60214da43578216c36a244b5fe63f2f5",
"assets/assets/images/reference/Unknown-10.png": "3786cbe4021d683330efb12e94d0a9db",
"assets/assets/images/reference/Unknown-12(1)(635%2520x%25201440%2520px).png": "effd5b5f5a461e726e559fdce949208d",
"assets/assets/images/reference/Unknown-14.png": "934f4fbd27e8445b5a72680150c9c85d",
"assets/assets/images/reference/Unknown-28.png": "40cf5878fa17d397049fec777e20814a",
"assets/assets/images/reference/logo_placeholder.png": "a4d6a853c53e7ce9f5c194663c583749",
"assets/assets/images/reference/Unknown-29.png": "68b5b999ec114c63378b2f0c65d56c43",
"assets/assets/images/reference/Unknown-15.png": "e333c7527ed527806ce8d7610abb2dee",
"assets/assets/images/reference/WelcomeScreen.svg": "406d3678e3cfdd0b042f77ab523fa53a",
"assets/assets/images/reference/Unknown-17.png": "8732020a20489a1c2149073571ff9f40",
"assets/assets/images/reference/Unknown-16.png": "cca8f0214f9e565c041b3818853c4ada",
"assets/assets/images/reference/Unknown-27.png": "033bc69db28a1fd7e2d482b31fe27d98",
"assets/assets/images/reference/Unknown-26.png": "c6b94a4ce79bfd7b4b73b9a5b8f74481",
"assets/assets/images/reference/Unknown-18.png": "4944c17cff946d5c48877c75bea255f2",
"assets/assets/images/reference/Unknown-24.png": "066e0d9f900fef655f44dddee69c5e92",
"assets/assets/images/reference/Unknown-30.png": "c22f0c5b72ca6ebb5fc0e4be0ea6d092",
"assets/assets/images/reference/Unknown-31.png": "2d3029ef36d2874d6cf020204a614539",
"assets/assets/images/reference/Unknown-25.png": "9727d48cda711da0b5ee3724893a3960",
"assets/assets/images/reference/Unknown-21.png": "919173db43fcb7268d4ec8db0df9b064",
"assets/assets/images/reference/Unknown-20.png": "7512a56a30ff09510f5e78aa81bd83b6",
"assets/assets/images/reference/Unknown-22.png": "977ed7d1d8bea9973e11b673ed2ac9f1",
"assets/assets/images/reference/Unknown-23.png": "e9d63aa7016fbdc7d39e9ccace2166e4",
"assets/assets/images/reference/Unknown-19(1).png": "b91fe3f55ac2dc97fd2aa540588e382f",
"assets/assets/images/reference/Unknown-24(635%2520x%25201440%2520px).png": "57ae8b7834d0e635747bb1396b535bb9",
"assets/assets/images/reference/Unknown-9.png": "217b53fd32d6e47ee4225eac2fd5e6d9",
"assets/assets/images/reference/Layout%2520v1.pdf": "a97ee71cb1170cd116630cd5d13242e7",
"assets/assets/images/reference/Unknown-8.png": "22a20e5f6cb98466be17c635cff37c57",
"assets/assets/images/img_vector_0_gray_600_02_39x39.svg": "7210ca93f88e2fcdcb6510178c2baf6e",
"assets/assets/images/img_image_38x38.png": "6b278687f2ffce0b0db1adf92aa46dcd",
"assets/assets/brand/icon_v1/gentlequest_web_192.png": "6d5a6c62c613a5a08802ab4cac849fa9",
"assets/assets/brand/icon_v1/gentlequest_android_1024.png": "6c7dce8ff342d5f61e8dac9632761ff9",
"assets/assets/brand/icon_v1/gentlequest_android_bg_1024.png": "10d877189ad100e92aa4ea86a7116df6",
"assets/assets/brand/icon_v1/gentlequest_web_512.png": "3010f6820d5582ed91fa3cae4f2d10a8",
"assets/assets/brand/icon_v1/gentlequest_ios_1024.png": "a26be0912832076ed21807d053892421",
"assets/assets/brand/icon_v1/gentlequest_favicon_32.png": "713fc25890616a8feade94feb8335357",
"assets/assets/brand/icon_v1/gentlequest_android_fg_1024.png": "0c958a43acd403e549ac85bdbd4cc49a",
"assets/assets/legal/privacy.md": "48d84c05ff12aa7101643d7eea2a09f8",
"assets/assets/legal/terms.md": "3455535e5f2adb2ad695b05462412795",
"assets/assets/fonts/InterMedium.ttf": "cad1054327a25f42f2447d1829596bfe",
"assets/assets/fonts/Fraunces/Fraunces.ttf": "df89c7ab0af2020b3949cf8a4bece47a",
"assets/assets/fonts/Fraunces/Fraunces-Italic.ttf": "d298a3dc03b97b862dd2c3af48f29496",
"assets/assets/fonts/Caveat/Caveat.ttf": "ccf2f844ded8bfd50efbed532a60d068",
"assets/assets/fonts/InterRegular.ttf": "ea5879884a95551632e9eb1bba5b2128",
"assets/assets/fonts/OFL.txt": "cd1a7cb90fac312616ab0a8c4a67f1bf",
"assets/assets/fonts/InterBold.ttf": "ba74cc325d5f67d0efbeda51616352db",
"canvaskit/skwasm.js": "ea559890a088fe28b4ddf70e17e60052",
"canvaskit/skwasm.js.symbols": "e72c79950c8a8483d826a7f0560573a1",
"canvaskit/canvaskit.js.symbols": "bdcd3835edf8586b6d6edfce8749fb77",
"canvaskit/skwasm.wasm": "39dd80367a4e71582d234948adc521c0",
"canvaskit/chromium/canvaskit.js.symbols": "b61b5f4673c9698029fa0a746a9ad581",
"canvaskit/chromium/canvaskit.js": "8191e843020c832c9cf8852a4b909d4c",
"canvaskit/chromium/canvaskit.wasm": "f504de372e31c8031018a9ec0a9ef5f0",
"canvaskit/canvaskit.js": "728b2d477d9b8c14593d4f9b82b484f3",
"canvaskit/canvaskit.wasm": "7a3f4ae7d65fc1de6a6e7ddd3224bc93"};
// The application shell files that are downloaded before a service worker can
// start.
const CORE = ["main.dart.js",
"index.html",
"flutter_bootstrap.js",
"assets/AssetManifest.bin.json",
"assets/FontManifest.json"];

// During install, the TEMP cache is populated with the application shell files.
self.addEventListener("install", (event) => {
  self.skipWaiting();
  return event.waitUntil(
    caches.open(TEMP).then((cache) => {
      return cache.addAll(
        CORE.map((value) => new Request(value, {'cache': 'reload'})));
    })
  );
});
// During activate, the cache is populated with the temp files downloaded in
// install. If this service worker is upgrading from one with a saved
// MANIFEST, then use this to retain unchanged resource files.
self.addEventListener("activate", function(event) {
  return event.waitUntil(async function() {
    try {
      var contentCache = await caches.open(CACHE_NAME);
      var tempCache = await caches.open(TEMP);
      var manifestCache = await caches.open(MANIFEST);
      var manifest = await manifestCache.match('manifest');
      // When there is no prior manifest, clear the entire cache.
      if (!manifest) {
        await caches.delete(CACHE_NAME);
        contentCache = await caches.open(CACHE_NAME);
        for (var request of await tempCache.keys()) {
          var response = await tempCache.match(request);
          await contentCache.put(request, response);
        }
        await caches.delete(TEMP);
        // Save the manifest to make future upgrades efficient.
        await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
        // Claim client to enable caching on first launch
        self.clients.claim();
        return;
      }
      var oldManifest = await manifest.json();
      var origin = self.location.origin;
      for (var request of await contentCache.keys()) {
        var key = request.url.substring(origin.length + 1);
        if (key == "") {
          key = "/";
        }
        // If a resource from the old manifest is not in the new cache, or if
        // the MD5 sum has changed, delete it. Otherwise the resource is left
        // in the cache and can be reused by the new service worker.
        if (!RESOURCES[key] || RESOURCES[key] != oldManifest[key]) {
          await contentCache.delete(request);
        }
      }
      // Populate the cache with the app shell TEMP files, potentially overwriting
      // cache files preserved above.
      for (var request of await tempCache.keys()) {
        var response = await tempCache.match(request);
        await contentCache.put(request, response);
      }
      await caches.delete(TEMP);
      // Save the manifest to make future upgrades efficient.
      await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
      // Claim client to enable caching on first launch
      self.clients.claim();
      return;
    } catch (err) {
      // On an unhandled exception the state of the cache cannot be guaranteed.
      console.error('Failed to upgrade service worker: ' + err);
      await caches.delete(CACHE_NAME);
      await caches.delete(TEMP);
      await caches.delete(MANIFEST);
    }
  }());
});
// The fetch handler redirects requests for RESOURCE files to the service
// worker cache.
self.addEventListener("fetch", (event) => {
  if (event.request.method !== 'GET') {
    return;
  }
  var origin = self.location.origin;
  var key = event.request.url.substring(origin.length + 1);
  // Redirect URLs to the index.html
  if (key.indexOf('?v=') != -1) {
    key = key.split('?v=')[0];
  }
  if (event.request.url == origin || event.request.url.startsWith(origin + '/#') || key == '') {
    key = '/';
  }
  // If the URL is not the RESOURCE list then return to signal that the
  // browser should take over.
  if (!RESOURCES[key]) {
    return;
  }
  // If the URL is the index.html, perform an online-first request.
  if (key == '/') {
    return onlineFirst(event);
  }
  event.respondWith(caches.open(CACHE_NAME)
    .then((cache) =>  {
      return cache.match(event.request).then((response) => {
        // Either respond with the cached resource, or perform a fetch and
        // lazily populate the cache only if the resource was successfully fetched.
        return response || fetch(event.request).then((response) => {
          if (response && Boolean(response.ok)) {
            cache.put(event.request, response.clone());
          }
          return response;
        });
      })
    })
  );
});
self.addEventListener('message', (event) => {
  // SkipWaiting can be used to immediately activate a waiting service worker.
  // This will also require a page refresh triggered by the main worker.
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
    return;
  }
  if (event.data === 'downloadOffline') {
    downloadOffline();
    return;
  }
});
// Download offline will check the RESOURCES for all files not in the cache
// and populate them.
async function downloadOffline() {
  var resources = [];
  var contentCache = await caches.open(CACHE_NAME);
  var currentContent = {};
  for (var request of await contentCache.keys()) {
    var key = request.url.substring(origin.length + 1);
    if (key == "") {
      key = "/";
    }
    currentContent[key] = true;
  }
  for (var resourceKey of Object.keys(RESOURCES)) {
    if (!currentContent[resourceKey]) {
      resources.push(resourceKey);
    }
  }
  return contentCache.addAll(resources);
}
// Attempt to download the resource online before falling back to
// the offline cache.
function onlineFirst(event) {
  return event.respondWith(
    fetch(event.request).then((response) => {
      return caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, response.clone());
        return response;
      });
    }).catch((error) => {
      return caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response != null) {
            return response;
          }
          throw error;
        });
      });
    })
  );
}
