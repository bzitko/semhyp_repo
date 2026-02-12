from .hyperedge import Atom, Hyperedge, hatom, hedge

def edge2txt(edge, subedge=None):

    def are_equal(arg1, arg2):
        if isinstance(arg1, type(arg2)):
            return arg1 == arg2
        return False


    def join(args, sep=" "):
        return sep.join(args)
    
    if edge.is_atom():
        return edge.label()
    
    conn, *args = edge
    txt_conn = edge2txt(conn)
    txt_args = [edge2txt(arg) for arg in args]
    conn_type = conn.type()

    if conn_type == "J":
        return join([join(txt_args[:-1], ","), txt_conn, txt_args[-1]])
    
    if conn_type == "Ml":
        return join(txt_args + [txt_conn])

    if conn_type[0] in ("T", "M"):
        return join([txt_conn] + txt_args)
    
    if conn_type == "Bp":
        txt_args[0] += txt_conn
        return join(txt_args)   
    
    if conn_type == "Jc":
        return txt_args[0]

    if conn_type in ("B", "Br", "Ba"):
        return join(txt_args)
                
    if conn_type[0] == "P":
        #roles = conn.predicate_atom().argroles().split(":") # dep srl proto lr
        roles = conn.argroles() # dep srl proto lr
        if not roles:
            roles = ("r" * len(args),)
        
        num_roles = len(roles)
        if len(roles) > 1:
            dep_roles, *_, lr_roles = roles
        else:
            dep_roles = roles[0]
            lr_roles = "r" * len(dep_roles)

        # if there is no lr_role, make it from the last
        if num_roles < 4: 
            lr_roles = ""
            num = str(min([int(r) for r in roles[-1] if r.isdigit()] + [9]))
            for r in roles[0]:
                lr_roles += "l" if r in "_s" + num else "r"
        
        lefts, rights = [], []
        for dep_role, lr_role, arg, txt_arg in zip(dep_roles, lr_roles, args, txt_args):
            if dep_role == "-":
                if not are_equal(arg, subedge):
                    continue
            if lr_role == "l":
                lefts.append(txt_arg)
            elif lr_role == "r":
                rights.append(txt_arg)

        return  join(lefts + [txt_conn] + rights)
    

    # EXTRA
    if conn_type == "Jr":
        if args[0] not in args[1]:
            return join(txt_args)
        return edge2txt(args[1], args[0])
    
    if conn_type == "C":
        return join([txt_conn] + txt_args)

    
    print("???", conn, conn_type)
    #raise Exception(f"Write IF THEN for {conn}")

        
