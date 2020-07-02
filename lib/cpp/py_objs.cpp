/////////////////////////////////////////////////////////////////////////////
// Representations of the application's Python modules, for use on CPP side.
//
// Author: Dustin Fast <dustin.fast@hotmail.com>
//
/////////////////////////////////////////////////////////////////////////////

#include <Python.h>


PyObject *get_pyclass(const char *name);


class CoordPredict {
    public:
        long int predict(void*);
        CoordPredict(const char*);
        ~CoordPredict();

    protected:
        PyObject *m_self;
};

CoordPredict::CoordPredict(const char *model_path) {
    setenv("PYTHONPATH", "/opt/app/src/lib/py/", 1);

    Py_Initialize();
    
    // Import py module and get class attribute
    PyObject *p_module = PyImport_ImportModule("coord_predict");
    assert(p_module != NULL);

    PyObject *p_class_attr = PyObject_GetAttrString(p_module, "CoordPredict");
    assert(p_class_attr != NULL);

    // Instantiate the class obj
    PyObject * p_class_obj = get_pyclass("CoordPredict");
    assert(p_class_obj != NULL);

    PyObject *p_class_args = Py_BuildValue("(s)", model_path);
    m_self = PyObject_CallObject(p_class_attr, p_class_args);
    assert(m_self != NULL);

    Py_DECREF(p_class_args);
    Py_DECREF(p_class_obj);
    Py_DECREF(p_class_attr);
    Py_DECREF(p_module);
}

CoordPredict::~CoordPredict() {
    Py_DECREF(m_self);
    Py_Finalize();
}

long int CoordPredict::predict(void *p) {
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