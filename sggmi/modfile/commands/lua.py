#Import
#Top Import

## LUA import statement adding
def lua_addimport(base, path):
    with open(base, "a") as basefile:
        basefile.write(f"\nImport {path}")