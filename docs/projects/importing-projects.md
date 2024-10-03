# Importing projects

When you launch `InsightBoard` for the first time it will create a folder called `InsightBoard/projects` in your home directory. This is where all your projects will be stored (you can change this location later from the Settings panel of the dashboard).

We recommend that you store each project in a separate (version controlled) git repository within the projects folder. This will allow you to easily share your project configuration with others and keep track of any changes made.

```{note}
Whether you share the data sources is entirely up to you as these can be version controlled, or maintained exclusively on the local machine.
```

To access an existing project from github (we supply a sample project called `sample_project`) in the `InsightBoard/projects` folder, you can run the following commands from the command line:

```bash
cd ~/InsightBoard/projects
git clone git@github.com:globaldothealth/InsightBoard-SampleProject.git sample_project
```

You can now start `InsightBoard`, where you should find `sample_project` in the projects list at the top of the dashboard.

```{note}
This requires that you have `git` installed on your machine and that you have access to the repository.

Alternatively, you can download the files from [https://github.com/globaldothealth/InsightBoard-SampleProject/archive/refs/heads/main.zip](https://github.com/globaldothealth/InsightBoard-SampleProject/archive/refs/heads/main.zip), unzip the archive, and place the folder in the `InsightBoard/projects` folder in your home directory, though this is not the recommended approach as it will make keeping your project up to date more difficult.
```
