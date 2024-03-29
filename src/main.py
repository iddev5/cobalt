# Cobalt Build System - 0.0.4
# Copyright (C) 2020, 2021 Ayush Bardhan Tripathy.
# This project is licensed under MIT License (See LICENSE.md).

import os, sys, subprocess, shutil;
import json, argparse;

#################################
# Config
#################################

def_build_dir = "builddir";
def_build_file = "build.ninja";
def_proj_file_name = "cobalt.json";
cobalt_version = "0.0.4";
ninja_required_version = "1.5.1";

#################################
# Project
#################################

properties = {
    "lang": "string",
    "src": "",
    "include_dir": "",
    "lib_dir": "",
    "libs": "",
    "runtime_data": "",
    "depends": "",
    "globalbuilddir": "string",
};

def check_for_prop(project, prop, type):
    if prop not in project:
        if type == "string": project[prop] = "";
        else: project[prop] = [];

def is_cpp(lang):
    return lang in ["cpp", "c++", "cxx"];

def load_project(path):
    project = {};
    project_file = os.path.join(path, def_proj_file_name);

    if not os.path.isfile(project_file):
        print("The current directory has no Cobalt project in it!\nAborting.");
        return None;

    with open(project_file) as file:
        project = json.load(file);

    build_dir = project["globalbuilddir"] if "globalbuilddir" in project else def_build_dir;

    project["path"] = path;
    project["build_dir"] = os.path.join(project["path"], build_dir);
    project["bin_dir"] = os.path.join(project["build_dir"], "bin");
    project["object_dir"] = os.path.join(project["build_dir"], "object");
    project["target_name"] = os.path.join(project["bin_dir"], project["id"]);

    for prop in properties:
        check_for_prop(project, prop, properties.get(prop));

    return project;

#################################
# Project creation
#################################

def is_valid_project_type(type):
    types = ["application", "staticlib", "sharedlib", "module"];
    if type in types:
        return True;
    else:
        return False;

def get_files(path, ext, recurse):
    ret = [];

    fold = path if path != "" else os.getcwd();
    for files in os.listdir(fold):
        name = os.path.join(path, files);
        if os.path.isfile(name):
            if name.endswith(ext): ret.append(name);
        elif recurse:
            ret.extend(get_files(name, ext, True));
    return ret;

def Cobalt_create(name, type):
    project = {};
    project["id"] = name;
    project["type"] = type;

    if os.path.isfile(def_proj_file_name):
        print("A project already exists in this directory.\nAbort.");
        return;

    if not is_valid_project_type(type):
        print("Unrecognized project type \"{}\", changing to default (application).".format(type));
        project["type"] = "application";

    project["src"]  = get_files("src", ".c", True) if os.path.exists("src") else [];
    project["src"] += get_files("", ".c", False);

    cpp_files = [];
    cpp_ext = [".cpp", ".cxx", ".cc"]
    for e in cpp_ext:
        cpp_files += get_files("src", e, True) if os.path.exists("src") else [];
        cpp_files += get_files("", e, False);

    if cpp_files != []:
        project["src"] += cpp_files;
        project["lang"] = "cpp";

    if os.path.exists("include"):
        project["include_dir"] = ["include"];

    if os.path.exists("lib"):
        project["lib_dir"] = ["lib"];
        # project["libs"]    = get_files("lib", ".so", False);

    if os.path.exists("runtime_data"):
        project["runtime_data"] = get_files("runtime_data", "", True);

    with open(def_proj_file_name, "w") as project_file:
        json.dump(project, project_file, indent = 4);

    print("New project created in current working directory: {}".format(name));

#################################
# Deleting build files
#################################

def Cobalt_clear(project):
    if not os.path.exists(project["build_dir"]):
        return;
    shutil.rmtree(project["build_dir"]);

#################################
# Generate project
#################################

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

def Ninja_write_file(project):
    file = [];

    file.extend([
        "# Cobalt Build System {}\n".format(cobalt_version),
        "# Repo: https://github.com/iddev5/cobalt\n",
        "# This file is generated automatically, do not edit!\n\n"
    ]);

    file.append("ninja_required_version = {}\n\n".format(ninja_required_version));

    file.extend([
        "rule c_Compile\n",
        " command = cc -MD -MQ $out -MF '$DEPFILE' $c_FLAGS $INCLUDE_DIR -o $out -c $in\n",
        " deps = gcc\n",
        " depfile = $DEPFILE\n",
        " description = Compiling C source$: $FILENAME\n\n"
    ]);

    file.extend([
        "rule cpp_Compile\n",
        " command = c++ -MD -MQ $out -MF '$DEPFILE' $c_FLAGS $INCLUDE_DIR -o $out -c $in\n",
        " deps = gcc\n",
        " depfile = $DEPFILE\n",
        " description = Compiling C++ source$: $FILENAME\n\n"
    ]);

    file.extend([
        "rule c_Link\n",
        " command = cc -o $out $in $LIB_DIR $LIBS\n",
        " description = Linking C project$: $LINKNAME\n\n"
    ]);

    file.extend([
        "rule cpp_Link\n",
        " command = c++ -o $out $in $LIB_DIR $LIBS\n",
        " description = Linking C++ project$: $LINKNAME\n\n"
    ]);

    include_dir = " ".join(make_include_dir(project.get("include_dir")));
    lib_dir = " ".join(make_lib_dir(project.get("lib_dir")));
    libs = " ".join(make_libs(project.get("libs")));

    cpp_proj = is_cpp(project.get("lang"));

    for i in range(len(project["src"])):
        source_name = project["source_list"][i];
        object_name = project["object_list"][i];

        if cpp_proj:
            file.extend([
                "build {}: cpp_Compile {}\n".format(object_name, source_name),
                " DEPFILE = {}\n".format(object_name + ".d"),
                " INCLUDE_DIR = {}\n".format(include_dir),
                " FILENAME = {}\n\n".format(project["src"][i])
            ]);
        else:
            file.extend([
                "build {}: c_Compile {}\n".format(object_name, source_name),
                " DEPFILE = {}\n".format(object_name + ".d"),
                " INCLUDE_DIR = {}\n".format(include_dir),
                " FILENAME = {}\n\n".format(project["src"][i])
            ]);

    cpp_link = "is_cpp_link" in project and project.get("is_cpp_link") == true;

    if cpp_link or cpp_proj:
        file.extend([
            "build {}: cpp_Link ".format(os.path.relpath(project["target_name"], project["build_dir"])),
            " ".join(project["object_list"]), "\n",
            " LIB_DIR = {}\n".format(lib_dir),
            " LIBS = {}\n".format(libs),
            " LINKNAME = {}\n\n".format(project["id"])
        ]);
    else:
        file.extend([
            "build {}: c_Link ".format(os.path.relpath(project["target_name"], project["build_dir"])),
            " ".join(project["object_list"]), "\n",
            " LIB_DIR = {}\n".format(lib_dir),
            " LIBS = {}\n".format(libs),
            " LINKNAME = {}\n\n".format(project["id"])
        ]);

    file.append("\n\n");

    return file;

def process_project(project):
    project["source_list"] = [];
    project["object_list"] = [];

    for source_file in project["src"]:
        file_name = os.path.join(project["path"], source_file);
        object_name = os.path.join("object", source_file.replace("/", "--") + ".o");

        if not os.path.isfile(file_name):
            print("File {} not found.\nAborting!".format(source_file));
            return False;

        project["source_list"].append(os.path.relpath(file_name, project["build_dir"]));
        project["object_list"].append(object_name);

def copy_runtime_data(project):
    for i in project["runtime_data"]:
        dest = os.path.join(project["bin_dir"], os.path.basename(i));

        if dest != project["target_name"]:
            if os.path.isfile(i):
                shutil.copyfile(i, dest);

def load_depends(project):
    for depend in project["depends"]:
        depproj = load_project(os.path.join(project["path"], depend));
        Cobalt_build(depproj);

        get_data = lambda prop: [os.path.relpath(os.path.join(depproj.get("path"), i), project.get("path")) for i in depproj.get(prop)];
        get_data_s = lambda prop: [os.path.relpath(os.path.join(depproj.get("path"), depproj.get(prop)), project.get("path")) if prop in depproj else []];

        if depproj["type"] == "application":
            project["runtime_data"].extend(get_data_s("target_name"));
        elif depproj["type"] == "module":
            project["include_dir"].extend(get_data("include_dir"));
            project["lib_dir"].extend(get_data("lib_dir"));
            project["libs"].extend(depproj["libs"]);
            project["is_cpp_link"] = is_cpp(depproj["lang"]);

        project["runtime_data"].extend(get_data("runtime_data"));

def Cobalt_generate(project):
    load_depends(project);

    process_project(project);
    file = Ninja_write_file(project);

    with open(os.path.join(project["build_dir"], def_build_file), "w") as f:
        f.writelines(file);

#################################
# Building project
#################################

def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path);

def Cobalt_build(project):
    make_dir(project["build_dir"]);
    make_dir(project["bin_dir"]);
    make_dir(project["object_dir"]);

    if project["type"] in ["application", "staticlib", "sharedlib"]:
        Cobalt_generate(project);
        subprocess.call(["ninja", "-f", def_build_file], cwd = project["build_dir"]);

    copy_runtime_data(project);

#################################
# Run project
#################################

def Cobalt_run(project, args):
    if project["type"] == "application":
        file_name = os.path.join(project["bin_dir"], project["id"]);
        if not os.path.isfile(file_name):
            print("Project is not compiled.");
            return False;

        print("Launching application: {}".format(project["id"]));
        cmd = [file_name] + args;
        subprocess.call(cmd);
    else:
        print("Nothing to run!");

    return True;

#################################
# Main
#################################

usage = """cobalt [-h] command

Simple, minimalistic build system for C projects.

list of commands:
  new         Create a new project
  clear       Clear the build directory
  build       Build the project in current directory
  rebuild     Clear the directory and build again
""";

def run(argv):
    ap = argparse.ArgumentParser(
        usage = usage
    );
    ap.add_argument("command", help = "Subcommand to run");

    args = ap.parse_args(argv[1:2]);

    if args.command == "new":
        nap = argparse.ArgumentParser();
        nap.add_argument("name", nargs = "?", default = os.path.basename(os.getcwd()));
        nap.add_argument("-t", "--type", type = str, default = "application");
        nargs = nap.parse_args(argv[2:]);

        Cobalt_create(nargs.name, nargs.type);
    else:
        proj_path = os.path.dirname(os.path.abspath(def_proj_file_name));

        project = load_project(proj_path);
        if project == None:
            return 0;

        if args.command == "clear":
            Cobalt_clear(project);

        elif args.command == "generate":
            Cobalt_generate(project);

        elif args.command == "build":
            Cobalt_build(project);

        elif args.command == "rebuild":
            Cobalt_clear(project);
            Cobalt_build(project);

        elif args.command == "run":
            if not Cobalt_run(project, argv[2:]):
                Cobalt_build(project);
                Cobalt_run(project, argv[2:]);
