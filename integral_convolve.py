import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from numpy.linalg import eig
from matplotlib.figure import figaspect
from matplotlib import rc

# matplotlib.rcParams['mathtext.default'] = 'regular'
matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.family'] = 'STIXGeneral'


def exp_kernel(distance):
    return np.exp(-distance)

def cross_correlation(n, kernel_func, lamb):
    """ Construct the full matrix (I+lambda*K) (dim n^2 x n^2) in the equation: g = (I+K)f"""
    result = np.zeros([n**2,n**2])
    for i in range(n**2):
        for j in range(n**2):
            result[i,j]= lamb*matrix_entry(i,j,n, kernel_func)
            if i==j:
                result[i,j] = result[i,j] + 1
    return result

def matrix_entry(i, j, n, kernel_func):
    """ Return the (i,j) entry of the matrix K(‖x−x′‖),
        where K is the kernel generated by kernel_func, which takes two 3d vectors as input. e.g. kernel(point2, point1) = log(distance)
        i, j =  0,1,..., n^2-1
        If self_interact is false, the K(x,x') is undefined -> set to 0 
    """
    x1 = (i//n)/n; y1 = (i%n)/n; point1 = np.array([x1,y1])
    x2 = (j//n)/n; y2 = (j%n)/n; point2 = np.array([x2,y2])

    diff = np.abs(point1-point2)
    distance = np.sum(np.where(diff<1/2, diff, 1-diff))    ## Manhatten distance on a wrap around lattice of size 1x1
    entry = (1/n**2)*kernel_func(distance)
    return entry

def get_cyclic_reps(N):
    """ Return regular representations of cyclic group, sorted in ascending order of group elements: i.e. 0,1,..N-1"""
    A = []
    for i in range(N-1,-1,-1):
        A.append([1 if j == i else 0 for j in range(N)])
    perms = []    
    for i in range(N):
        perms.append(np.array([A[i-j] for j in range(N)]))
    I = perms.pop(-1)
    return [I] + perms

def get_cyclic_product_reps(N):
    """ Return INVERSE regular representations (permutation matrices of size N^2 x N^2) of the direct product of a cyclic group to itself, 
            sorted in ascending order of group elements: i.e. (0,0),(0,1),,..(N-1,N-1)"""
    group1 = get_cyclic_reps(N)
    group2 = get_cyclic_reps(N)
    reps = []
    for mat1 in group1:
        for mat2 in group2:
            reps.append(np.kron(mat1, mat2))
    sorted_reps = sorted(reps, key= lambda mat: np.argmax(mat[:,0]))
    return [rep.T for rep in sorted_reps]

def get_filter(N, kernel_func, lamb):
    """ first column of cross-correlation matrix"""
    m = [lamb*matrix_entry(0, 0, N, kernel_func)+1]
    for j in range(1,N**2):
            m.append(lamb*matrix_entry(0,j,N, kernel_func))
    return np.array(m)

def f(x, y):
    """ Function on lattice to be solved."""
    return (x-x**3)*(y-y**3)

def g(x,y, lamb):
    """ LHS of integral equation."""
    # def func(x):
    #     if x==0:
    #         return 0
    #     else:
    #         return np.exp(-x**2)*(-3+2*x**2+np.exp(2*x)*(3-6*x+4*x**2))/(8*x**4)        
    def func(x):
        if x >= 0 and x<0.5:
            return -3*np.exp(-x)-2*x*(5+x**2)+(1+2*x)*(21+4*x*(1+x))/(4*np.exp(1/2))
        elif x>=0.5 and x<=1:
            return 9*np.exp(-1+x)-2*x*(5+x**2)+(-1+2*x)*(21+4*x*(-1+x))/(4*np.exp(1/2))
        else:
            raise Exception("should not get here")
    vfunc = np.vectorize(func)
    return f(x, y) + lamb*vfunc(x)*vfunc(y)

def discretized_f(N):
    vec = []
    for i in range(N):
        for j in range(N):
            vec.append(f(i/N, j/N))
    return np.array(vec)

def discretized_g(lamb, N):
    vec = []
    for i in range(N):
        for j in range(N):
            vec.append(g(i/N, j/N, lamb))
    return np.array(vec)

# N1=50
# X,Y = np.meshgrid(1/N1*np.array(list(range(N1))), 1/N1*np.array(list(range(N1))))
# Z = g(X, Y, 1)
# plt.figure()
# ax = plt.axes(projection='3d')
# ax.plot_wireframe(X, Y, Z, color='blue', alpha=0.8)
# plt.show()


def plot_solution():
    kernel = exp_kernel
    lamb = 1
    fig = plt.figure(figsize=(8.2,2.3))
    err = []   

    for index, n in enumerate([4,16,64]):
        ######### Verifying the matrix is indeed a group cross-correlation    
        # reps = get_cyclic_product_reps(n)
        # filter = get_filter(n, kernel, lamb)
        # approx = np.zeros([n**2, n**2])
        # for i in range(n**2):
        #    approx = approx + filter[i]*reps[i]

        A = cross_correlation(n, kernel, lamb)
        # print(np.linalg.norm(approx-A, ord='fro')/(n**4))

        g_vec = discretized_g(lamb, n)
        sol = np.reshape(np.linalg.inv(A)@np.array([g_vec]).T,-1)

        eigs, _ = np.linalg.eig(A)
        kappa = np.max(np.abs(eigs))/np.min(np.abs(eigs))
        print("n = " + str(n))
        print("Condition number = " + str(np.round(kappa,4)))
        print("Minimum singular value magnitude  = "np.min(np.abs(eigs)))

        f_vec = discretized_f(n)
        err.append(np.mean(np.abs(sol-f_vec)))

        ##### 3D plots  
        xs = np.repeat(1/n*np.array(list(range(n))),n)
        ys = np.tile(1/n*np.array(list(range(n))),n)
        

        ax = fig.add_subplot(1, 3, index+1, projection='3d')
        ax.grid(False)
        ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        
        dot_size = 32/n
        ax.scatter(xs, ys, sol, c=sol, label = "approx",cmap='autumn', marker= ".", alpha = 0.99, s=dot_size)  

        N1 = 1000
        X,Y = np.meshgrid(1/N1*np.array(list(range(N1))), 1/N1*np.array(list(range(N1))))
        Z = f(X, Y)
        ax.plot_surface(X, Y, Z, color='steelblue', alpha=0.5, linewidth=0)  #, cmap=matplotlib.cm.Blues
        res = 1000
        x = np.linspace(0, (N1-1)/N1, res)
        ax.plot(x, 0*np.ones(res), f(x, 0), color='steelblue', lw=0.4, zorder=5)
        ax.plot(x, (N1-1)/N1*np.ones(res), f(x, (N1-1)/N1), color='steelblue', lw=0.4, zorder=5)
        ax.plot(0*np.ones(res), x, f(0, x), color='steelblue', lw=0.4, zorder=5)
        ax.plot((N1-1)/N1*np.ones(res), x, f((N1-1)/N1, x), color='steelblue', lw=0.4, zorder=5)

        # ax.set_title(rf'$n$ = {n}')
        plt.subplots_adjust(left=0, right=0.7, bottom=0, top=0.7, wspace=0, hspace=0)
        # ax.set_xlim(np.array([-1,1]))
        # ax.set_ylim(np.array([-1,1]))
        # ax.set_zlim(np.array([-1,1]))
        ax.azim = -60
        ax.dist = 12
        ax.elev = 12
        ax.set_xlabel(r'$t_1$',fontsize= 10,labelpad=0.3)
        ax.set_ylabel(r"$t_2$",fontsize= 10, labelpad=0.3)
        ax.set_zlabel(r"$f(t_1, t_2$)",fontsize= 10, labelpad = 0.3)
        plt.tick_params(axis='x', labelsize= 8, pad = 0)
        plt.tick_params(axis='y', labelsize= 8, pad = 0)
        plt.tick_params(axis='z', labelsize= 8, pad = 0)
        plt.xticks([0, 0.5, 1 ], ['0', '0.5','1'],fontsize= 8)
        plt.yticks([0, 0.5, 1 ], ['0', '0.5','1'],fontsize= 8)
        plt.locator_params(axis='z', nbins=4)
        plt.setp(ax.spines.values(), linewidth=0.4)
        ax.xaxis.set_rotate_label(False)
        ax.yaxis.set_rotate_label(False)
        # ax.zaxis.set_rotate_label(False)
        ax.text(0.5,0.5,0.185, rf'$n={n}$', fontsize = 10)
    plt.savefig("solution.pdf",bbox_inches='tight')

def plot_error():
    kernel = exp_kernel
    lamb = 1
    fig = plt.figure(figsize=(5.2,3.5))
    err = []   
    ns = np.array([4,8,16,32,64])
    for index, n in enumerate(ns):
        ######### Verifying the matrix is indeed a group cross-correlation    
        # reps = get_cyclic_product_reps(n)
        # filter = get_filter(n, kernel, lamb)
        # approx = np.zeros([n**2, n**2])
        # for i in range(n**2):
        #    approx = approx + filter[i]*reps[i]

        A = cross_correlation(n, kernel, lamb)
        # print(np.linalg.norm(approx-A, ord='fro')/(n**4))

        g_vec = discretized_g(lamb, n)
        sol = np.reshape(np.linalg.inv(A)@np.array([g_vec]).T,-1)

        eigs, _ = np.linalg.eig(A)
        kappa = np.max(np.abs(eigs))/np.min(np.abs(eigs))
        print("n = " + str(n))
        print("Condition number = " + str(np.round(kappa,4)))
        # print(np.max(np.abs(eigs)))

        f_vec = discretized_f(n)
        err.append(np.mean(np.abs(sol-f_vec)))
    err = np.array(err)
    plt.plot(ns, err, 'o', zorder=5)

    logx = np.log10(ns); logy = np.log10(err)
    coeffs = np.polyfit(logx,logy,deg=1); poly = np.poly1d(coeffs); yfit = lambda x: 10**(poly(np.log10(x)))
    a = np.round(coeffs[0],2); b = np.round(coeffs[1],2)
    plt.plot(ns,yfit(ns), "--", color = 'grey')
    plt.yscale("log")
    plt.xscale("log")
    plt.text(10,0.0005, rf"${a} \log n {b}$", fontsize = 10)
    plt.xlabel(r"$n$", fontsize= 10)
    plt.ylabel(r"$\frac{\Vert\mathbf{f}-f(\mathbf{t})\Vert_1}{n^2}$", fontsize=13, labelpad=0.01)
    # plt.show()
    plt.savefig("error.pdf")


if __name__ == "__main__":
    plot_error()









