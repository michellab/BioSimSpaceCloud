# Fn function to run a gromacs simulation

## Docker image

First, there is a docker image controlled by Dockerfile. This compiles
and install gromacs and Fn. The Fn is controlled by a Python function
in func.py

## Building

Build using docker to make sure it is ok using

```
# docker build .
```

## Fn building

The Fn function build is controlled using `func.yaml`. To build the
function you must run

```
# fn build
```

This will build the application. Test using

```
# fn run
```

or put in info using

```
# echo -n '{"name":"Chris"}' | fn run
```

Once happy, make sure that the docker repository has been set up, e.g.

```
# export FN_REGISTRY=chryswoods
```

and then deploy the app using

```
# fn deploy --app gromacs
```

You can test it is properly deployed using

```
# fn call gromacs /gromacs
```

or from the web browser go to

```
http://130.61.60.88:8080/r/gromacs/gromacs
```

