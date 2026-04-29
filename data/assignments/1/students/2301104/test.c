#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
typedef int Type;
typedef struct node_t* Node;
struct node_t{
 Type data;
 Node next;   
};
Node newNode(Type data,Node next)
{
    Node node=(Node)calloc(1,sizeof(struct node_t));
    assert(node);
    node->data=data;
    node->next=next;
    return node;
}

Node addFirst(Node node,Type data){
    return newNode(data,node);
}

void printList(Node node){
    if(!node)
    printf("NULL\n");
    for(;node;node=node->next)
    printf("%d -> ",node->data);
    printf("NULL\n");
}
int countEle(Node node){
    int count=0;
    for(;node;node=node->next){
        count++;
    }
    return count;
}
Node removeFirst(Node node,Type *pData,int *pStatus){
    if(!node){
        *pStatus=0;
    return NULL;}
    *pData=node->data;
    *pStatus=1;
    Node p=node->next;
    free(node);
    return p;
}

Node addLast(Node node,Type data){
    if(!node)
    return addFirst(node,data);
    Node p=node;
    for(;p->next;p=p->next)
    ;
    p->next=newNode(data,NULL);
    return node;
}
Node removeLast(Node node,Type *pData,int *pStatus){
    if(!node || !node->next)
    return removeFirst(node,pData,pStatus);
    Node p=node;
    for(;p->next->next;p=p->next)
    ;
    *pData=p->next->data;
    *pStatus=1;
    free(p->next);
    p->next=NULL;
    return node;
}
void getEle(Node node,int ind){
    Node p=node;
    int i;
    int count=countEle(node);
    if(ind>count)
    printf("NULL\n");
    for(i=0;i<ind;i++)
    {
        
       p=p->next; 
    }
    printf("%d\n",p->data);
}
Node setEle(Node node,int ind,Type data){
    Node p=node;
    int i;
    int count=countEle(node);
    if(ind>count)
    return NULL;
    for(i=0;i<ind;i++)
    {
        //if(!node)
        //return NULL;
        p=p->next;
    }
    p->data=data;
    return node;

}
Node addInd(Node node,Type data,int ind){
    int i;
    if(!node|| ind==0)
    return addFirst(node,data);
    Node p=node;
    for(i=1;i<ind;i++){
        p=p->next;
    }

    p->next=newNode(data,p->next);
    
    return node;

}

Node removeInd(Node node,int ind){
    int i;
    if(!node)
    return NULL;
    Node p=node;
    for(i=1;i<ind;i++)
    {
        p=p->next;
    }
    Node temp=p->next;
    p->next=p->next->next;
    free(temp);
    temp=NULL;
    
    //node->next=temp;
    return node;
    
}

Node addVal(Node node,Type data,Type value){
    Node p=node;
    if(!node)
    return addFirst(node,data);
    for(;p;p=p->next){
        if(p->data==value){
            p->next=newNode(data,p->next);
            break;
        }
    }
    return node;
}

Node remVal(Node node,Type value){
    if(!node){
        return NULL;
    }
    Node p=node;
    for(;p;p=p->next)
    {
        if(p->next->data==value)
        {
            Node temp=p->next;
            p->next=p->next->next;
            free(temp);
            temp=NULL;
            break;
        }
    }
    return node;
}
Node reverse(Node node)
{
    Node p=node,prev=NULL,next;
    while(p!=NULL){
     next=p->next;
     p->next=prev;
     prev=p;
     p=next;  
    }
     return prev;
}

void recurprint(Node node){
    if(node==NULL)
    return;
    printf("%d -> ",node->data);
    //if(node)
    recurprint(node->next);
    
}

void recurrev(Node node){
    if(node==NULL)
    return;
    recurrev(node->next);
    printf("%d -> ",node->data);
    
}

Node revrec(Node node,Node prev){
    if(node==NULL){
        return prev;
    }
    Node next=node->next;
    node->next=prev;
    return revrec(next,node);
}


Node insertSorted(Node node, Type data) {
    Node temp = newNode(data,node);

    if (node == NULL || data < node->data) {
        temp->next = node;
        node = temp;
        return;
    }
    Node current = node;
    while (current->next != NULL && current->next->data < data) {
        current = current->next;
    }
    temp->next = current->next;
    current->next = temp;
    return temp;
}
Node sortList(Node node){
    Node temp=node,new;
    Type data;
    if(!node){
        return node;
    }
    new=newNode(node->data,NULL);
    node=node->next;
    for(;node;node=node->next){
        data=node->data;
        new=insertSorted(new,data);
    }
    return new;
}

int main()
{
    Type data = 0;
    int status = 0;

    Node list = NULL;
    Node sorted_list = NULL;

    int n;
    scanf("%d", &n);

    Type *arr = NULL;

    if (n > 0)
    {
        arr = (Type *)malloc(n * sizeof(Type));
        assert(arr);

        for (int i = 0; i < n; i++)
        {
            scanf("%d", &arr[i]);
        }

        for (int i = n - 1; i >= 0; i--)
        {
            list = addFirst(list, arr[i]);
        }

        free(arr);
    }

    printf("Original list:\n");
    printList(list);

    printf("Count:\n");
    printf("%d\n", countEle(list));

    printf("After removing first:\n");
    list = removeFirst(list, &data, &status);
    printList(list);

    int end_value;
    scanf("%d", &end_value);

    printf("After adding at end:\n");
    list = addLast(list, end_value);
    printList(list);

    printf("After removing last:\n");
    list = removeLast(list, &data, &status);
    printList(list);

    int get_pos;
    scanf("%d", &get_pos);

    printf("Element at position:\n");
    getEle(list, get_pos);

    int set_pos;
    Type set_value;
    scanf("%d %d", &set_pos, &set_value);

    printf("After setting element:\n");
    list = setEle(list, set_pos, set_value);
    printList(list);

    int add_pos;
    Type add_value;
    scanf("%d %d", &add_pos, &add_value);

    printf("After adding element at position:\n");
    list = addInd(list, add_value, add_pos);
    printList(list);

    int remove_pos;
    scanf("%d", &remove_pos);

    printf("After removing element at position:\n");
    list = removeInd(list, remove_pos);
    printList(list);

    Type add_key, value_after_key;
    scanf("%d %d", &add_key, &value_after_key);

    printf("After adding after first occurrence:\n");

    list = addVal(list, value_after_key, add_key);
    printList(list);

    Type remove_key;
    scanf("%d", &remove_key);

    printf("After removing first occurrence:\n");
    list = remVal(list, remove_key);
    printList(list);

    printf("After iterative reverse:\n");
    list = reverse(list);
    printList(list);

    printf("After sorting:\n");
    list = sortList(list);
    printList(list);

    printf("Recursive print:\n");
    recurprint(list);
    printf("NULL\n");

    printf("Recursive reverse print:\n");
    recurrev(list);
    printf("NULL\n");

    printf("After recursive physical reverse:\n");
    list = revrec(list, NULL);
    printList(list);

    int sorted_n;
    scanf("%d", &sorted_n);

    Type *sorted_arr = NULL;

    if (sorted_n > 0)
    {
        sorted_arr = (Type *)malloc(sorted_n * sizeof(Type));
        assert(sorted_arr);

        for (int i = 0; i < sorted_n; i++)
        {
            scanf("%d", &sorted_arr[i]);
        }

      
        for (int i = sorted_n - 1; i >= 0; i--)
        {
            sorted_list = addFirst(sorted_list, sorted_arr[i]);
        }

        free(sorted_arr);
    }

    printf("Sorted list:\n");
    printList(sorted_list);

    Type insert_sorted_value;
    scanf("%d", &insert_sorted_value);

    printf("After sorted insertion:\n");
    sorted_list = insertSorted(sorted_list, insert_sorted_value);
    printList(sorted_list);

    return 0;
}