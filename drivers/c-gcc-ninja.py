import os

def make_prefix(dir_list, prefix):
    if dir_list == None: 
        return [];
    else:
        to_ret = [];
        to_ret.extend([prefix + i for i in dir_list]);
        return to_ret;

def make_include_dir(include_dir_list):
    return make_prefix(include_dir_list, "-I");

def make_lib_dir(lib_dir_list):
    return make_prefix(lib_dir_list, "-L");

def make_libs(libs_list):
    return make_prefix(libs_list, "-l");

def wrap_cmd(cmd):
    if os.name == "nt":
        return "cmd /c \"" + cmd + "\"";
    return cmd;

def write_rules(info):
    file = [];

    file.extend([
        "# Cobalt Build System {}\n".format(info["cobalt_version"]),
        "# Repo: https://github.com/iddev5/cobalt\n",
        "# This file is generated automatically, do not edit!\n\n"
    ]);

    file.append("ninja_required_version = {}\n\n".format(info["ninja_required_version"]));
        
    file.extend([
        "rule c_Compile\n",
        " command = cc -MD -MQ $out -MF '$DEPFILE' $c_FLAGS $INCLUDE_DIR -o $out -c $in\n",
        " deps = gcc\n",
        " depfile = $DEPFILE\n",
        " description = Compiling file$: $FILENAME\n\n"
    ]);

    file.extend([
        "rule c_Link\n",
        " command = cc -o $out $in $LIB_DIR $LIBS\n",
        " description = Linking project$: $LINKNAME\n\n"
    ]);

    return file;


def Write_file(project, info):
    file = write_rules(info);
   
    include_dir = " ".join(make_include_dir(project.get("include_dir")));
    lib_dir = " ".join(make_lib_dir(project.get("lib_dir")));
    libs = " ".join(make_libs(project.get("libs")));

    for i in range(len(project["src"])):
        source_name = project["source_list"][i];
        object_name = project["object_list"][i];

        file.extend([
            "build {}: c_Compile {}\n".format(object_name, source_name),
            " DEPFILE = {}\n".format(object_name + ".d"),
            " INCLUDE_DIR = {}\n".format(include_dir),
            " FILENAME = {}\n\n".format(project["src"][i])
        ]);
        
    file.extend([
        "build {}: c_Link ".format(os.path.relpath(project["target_name"], project["build_dir"])),
        " ".join(project["object_list"]), "\n",
        " LIB_DIR = {}\n".format(lib_dir),
        " LIBS = {}\n".format(libs),
        " LINKNAME = {}\n\n".format(project["id"])
    ]);

    file.append("\n\n");

    return file;
