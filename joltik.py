import requests, re, argparse, zipfile, shutil, os, operator, tempfile

MIRROR_URL = "https://mirror.unownhash.com"

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Joltik")
    parser.add_argument(
        "--arch",
        help="which arch to use. either arm64-v8a, or armeabi-v7a",
        type=str,
        default="arm64-v8a",
    )
    parser.add_argument(
        "--version",
        help="which version to get. specify x.xxx.x. if not provided, latest is used by default",
        type=str,
        default="latest",
    )
    args = parser.parse_args()
    POGO_VER = None
    ARCH = args.arch
    
    VERSIONS = requests.get(f"{MIRROR_URL}/index.json").json()
    # a hack to fix the index.json version fields containing apkm
    VERSIONS = [{**v, "version": v["version"].replace(".apkm", "")} for v in VERSIONS]
    # sort newest to oldest, just in case
    VERSIONS = sorted(
        VERSIONS, key=lambda x: float(x["version"].split(".", 1)[1]), reverse=True
    )

    if args.version == "latest":
        try:
            POGO_VER = next(filter(lambda x: x["arch"] == ARCH, VERSIONS))
            print(f"Requested latest version for {ARCH} is {POGO_VER['version']}.")
        except StopIteration:
            print(f"Unable to find a version on the mirror for arch {ARCH}")
            exit(1)
    else:
        try:
            POGO_VER = next(
                filter(
                    lambda x: x["version"] == args.version and x["arch"] == ARCH,
                    VERSIONS,
                )
            )
        except StopIteration:
            print(
                f"Version {args.version} with arch {ARCH} does not exist on the mirror."
            )
            exit(1)

    IS_APKM = POGO_VER["filename"].endswith(".apkm")
    TMP_DIR = tempfile.mkdtemp()

    DOWNLOAD_URL = MIRROR_URL + f"/apks/{POGO_VER['filename']}"

    with open(f"{TMP_DIR}/pogo.zip", "wb") as f:
        pogo_apk = requests.get(DOWNLOAD_URL)
        f.write(pogo_apk.content)
    if not IS_APKM:
        with zipfile.ZipFile(f"{TMP_DIR}/pogo.zip", "r") as z:
            z.extract(f"lib/{ARCH}/libNianticLabsPlugin.so", path=TMP_DIR)
    else:
        # need to extract twice, first the apkm and then the split apk inside of it to get to the lib
        with zipfile.ZipFile(f"{TMP_DIR}/pogo.zip", "r") as z:
            z.extract(f"split_config.{ARCH.replace('-', '_')}.apk", path=TMP_DIR)
        with zipfile.ZipFile(
            f"{TMP_DIR}/split_config.{ARCH.replace('-', '_')}.apk"
        ) as z:
            z.extract(f"lib/{ARCH}/libNianticLabsPlugin.so", path=TMP_DIR)

    # copy into arch folder
    if not os.path.exists(ARCH):
        os.makedirs(ARCH)

    shutil.copyfile(
        f"{TMP_DIR}/lib/{ARCH}/libNianticLabsPlugin.so",
        f"./{ARCH}/libNianticLabsPlugin.so",
    )

    shutil.rmtree(TMP_DIR)
    print(f"Successfuly downloaded version {POGO_VER['version']} for arch {ARCH}.")
