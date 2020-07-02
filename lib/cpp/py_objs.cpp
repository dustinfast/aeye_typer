/////////////////////////////////////////////////////////////////////////////
// Representations of the application's Python modules, for use on CPP side.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#include <Python.h>


PyObject *get_pyclass(const char *name);


class EyeTrackerCoordPredict {
    public:
        long int predict(void*);
        EyeTrackerCoordPredict(const char*);
        ~EyeTrackerCoordPredict();

    protected:
        PyObject *m_self;
};

EyeTrackerCoordPredict::EyeTrackerCoordPredict(const char *model_path) {
    setenv("PYTHONPATH", "/opt/app/src/lib/py/", 1);

    Py_Initialize();
    
    // Import py module and get class attribute
    PyObject *p_module = PyImport_ImportModule("eyetracker_coord_predict");
    assert(p_module != NULL);

    PyObject *p_attr = PyObject_GetAttrString(p_module, "EyeTrackerCoordPredict");
    assert(p_attr != NULL);

    // Instantiate the class obj
    PyObject * p_obj = get_pyclass("EyeTrackerCoordPredict");
    assert(p_obj != NULL);

    PyObject *p_args = Py_BuildValue("(s)", model_path);
    m_self = PyObject_CallObject(p_attr, p_args);
    assert(m_self != NULL);

    Py_DECREF(p_args);
    Py_DECREF(p_obj);
    Py_DECREF(p_attr);
    Py_DECREF(p_module);
}

EyeTrackerCoordPredict::~EyeTrackerCoordPredict() {
    Py_DECREF(m_self);
    Py_Finalize();
}

long int EyeTrackerCoordPredict::predict(void *p) {
    // TODO: Implement fully
    PyObject *p_res = PyObject_CallMethod(m_self, "predict", "(ii)", 1, 3);
    assert(p_res != NULL);

    long int pred = PyLong_AsLong(p_res);
    Py_DECREF(p_res);

    return pred;
}


PyObject* get_pyclass(const char *name)
{
    PyObject* p_name = PyUnicode_FromString(name);
    PyObject* p_base = PyTuple_New(0);
    PyObject* p_dict = PyDict_New();

    PyObject *pClass = PyObject_CallFunctionObjArgs(
        (PyObject *)&PyType_Type, p_name, p_base, p_dict, NULL);

    Py_DECREF(p_name);
    Py_DECREF(p_base);
    Py_DECREF(p_dict);

    return pClass;

}