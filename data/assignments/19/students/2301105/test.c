#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

typedef struct Node_t* Node;

struct Node_t {
    int data;
    Node next;
};

Node newnode(int data, Node next) {
    Node node = (Node)calloc(1, sizeof(struct Node_t));
    assert(node);
    node->data = data;
    node->next = next;
    return node;
}

Node addfirst(Node node, int data) {
    return newnode(data, node);
}

void printlist(Node node) {
    printf("\n");
    if (!node) {
        printf("NULL\n");
        return;
    }

    Node current = node;
    while (current != NULL) {
        printf("%d -> ", current->data);
        current = current->next;
    }
    printf("NULL\n");
}

void count(Node node) {
    int count = 0;
    Node current = node;
    while (current != NULL) {
        current = current->next;
        count++;
    }
    printf("length of the list: %d\n", count);
}

Node remfir(Node node) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }
    Node newHead = node->next;
    free(node);
    return newHead;
}

Node addlast(Node node, int data) {
    if (!node) {
        return addfirst(NULL, data);
    }

    Node current = node;
    while (current->next != NULL) {
        current = current->next;
    }

    current->next = newnode(data, NULL);
    return node;
}

Node remlast(Node node) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    Node current = node;
    while (current->next != NULL && current->next->next != NULL) {
        current = current->next;
    }

    free(current->next);
    current->next = NULL;
    return node;
}

void geti(Node node, int n) {
    if (!node) {
        printf("No list\n");
        return;
    }

    Node current = node;
    int count = 1;
    while (count < n && current != NULL) {
        current = current->next;
        count++;
    }

    if (current != NULL) {
        printf("The %dth element is: %d\n", n, current->data);
    } else {
        printf("Invalid position\n");
    }
}

Node addi(Node node, int n, int data) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    if (n == 1) {
        return addfirst(node, data);
    }

    Node current = node;
    int count = 1;

    while (count < n - 1 && current != NULL) {
        current = current->next;
        count++;
    }

    if (current != NULL) {
        current->next = newnode(data, current->next);
    }

    return node;
}

Node seti(Node node, int n, int data) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    Node current = node;
    int count = 1;
    while (count < n && current != NULL) {
        current = current->next;
        count++;
    }

    if (current != NULL) {
        current->data = data;
    }

    return node;
}

Node remi(Node node, int n) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    if (n == 1) {
        Node newHead = node->next;
        free(node);
        return newHead;
    }

    Node current = node;
    int count = 1;
    while (count < n - 1 && current != NULL) {
        current = current->next;
        count++;
    }

    if (current != NULL && current->next != NULL) {
        Node temp = current->next;
        current->next = temp->next;
        free(temp);
    }

    return node;
}

Node addkey(Node node, int key, int data) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    Node current = node;

    while (current != NULL) {
        if (current->data == key) {
            current->next = newnode(data, current->next);
            break;
        }
        current = current->next;
    }

    return node;
}

Node remkey(Node node, int key) {
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    Node current = node;

    while (current != NULL) {
        if (current->next->data == key) {
            current->next = current->next->next;
            break;
        }
        current = current->next;
    }

    return node;
}

Node reverse(Node node)
{
    if (!node) {
        printf("NULL\n");
        return NULL;
    }

    Node current = node;
    Node prev = NULL;
    Node next = NULL;

    while (current != NULL) {
        next = current->next;
        current->next = prev;
        prev = current;
        current = next;
    }
    node=prev;

    return node;
}


Node sortlist(Node node) {
    int swaped;
    Node ptr1;
    Node lptr = NULL;

    if (!node)
        return NULL;

    while (1) {
        swaped = 0;
        ptr1 = node;

        while (ptr1->next != lptr) {
            if (ptr1->data > ptr1->next->data) {
                int temp = ptr1->data;
                ptr1->data = ptr1->next->data;
                ptr1->next->data = temp;
                swaped = 1;
            }
            ptr1 = ptr1->next;
        }

        if (!swaped) {
            break;
        }

        lptr = ptr1;
    }

    return node;
}

void printlistrec(Node node)
{
    if(node == NULL){
       printf("NULL");
       return ;}

    printf("%d -> ",node->data);
    printlistrec(node->next);

}

void printlistrecrev(Node node)
{
    if(node == NULL){
       printf("NULL->");
       return ;}
    printlistrecrev(node->next);
    printf("%d -> ",node->data);

}

Node insersort(Node node , int key)
{
     if (!node) {
        printf("NULL\n");
        return NULL;
    }

    Node current = node;

    while (current != NULL) {
       if(current->data <= key)
       {
           current->next=newnode(key , current->next);
           break;
       }
        current = current->next;
    }

    return node;
}

Node recrevlist(Node node) {

    if (node == NULL || node->next == NULL) {
        return node;
    }

    Node restReversed = recrevlist(node->next);


    node->next->next = node;
    node->next = NULL;


    return restReversed;
}



int main() {
    Node list = NULL;
    Node list2 = NULL;

    int n;
    scanf("%d", &n);

    int *arr = NULL;

    if (n > 0) {
        arr = (int *)malloc(n * sizeof(int));
        assert(arr);

        for (int i = 0; i < n; i++) {
            scanf("%d", &arr[i]);
        }

        for (int i = n - 1; i >= 0; i--) {
            list = addfirst(list, arr[i]);
        }

        free(arr);
    }

    printf("Original list:");
    printlist(list);

    printf("Count:\n");
    count(list);

    printf("After removing first:");
    list = remfir(list);
    printlist(list);

    int end_value;
    scanf("%d", &end_value);

    printf("After adding at end:");
    list = addlast(list, end_value);
    printlist(list);

    printf("After removing last:");
    list = remlast(list);
    printlist(list);

    int get_pos;
    scanf("%d", &get_pos);

    printf("Element at position:\n");

    geti(list, get_pos + 1);

    int set_pos, set_value;
    scanf("%d %d", &set_pos, &set_value);

    printf("After setting element:");

    list = seti(list, set_pos + 1, set_value);
    printlist(list);

    int add_pos, add_value;
    scanf("%d %d", &add_pos, &add_value);

    printf("After adding element at position:");
 
    list = addi(list, add_pos + 1, add_value);
    printlist(list);

    int remove_pos;
    scanf("%d", &remove_pos);

    printf("After removing element at position:");
 
    list = remi(list, remove_pos + 1);
    printlist(list);

    int add_key, value_after_key;
    scanf("%d %d", &add_key, &value_after_key);

    printf("After adding after first occurrence:");
    list = addkey(list, add_key, value_after_key);
    printlist(list);

    int remove_key;
    scanf("%d", &remove_key);

    printf("After removing first occurrence:");
    list = remkey(list, remove_key);
    printlist(list);

    printf("After iterative reverse:");
    list = reverse(list);
    printlist(list);

    printf("After sorting:");
    list = sortlist(list);
    printlist(list);

    printf("Recursive print:\n");
    printlistrec(list);
    printf("\n");

    printf("Recursive reverse print:\n");
    printlistrecrev(list);
    printf("\n");

    printf("After recursive physical reverse:");
    list = recrevlist(list);
    printlist(list);

    int sorted_n;
    scanf("%d", &sorted_n);

    int *sorted_arr = NULL;

    if (sorted_n > 0) {
        sorted_arr = (int *)malloc(sorted_n * sizeof(int));
        assert(sorted_arr);

        for (int i = 0; i < sorted_n; i++) {
            scanf("%d", &sorted_arr[i]);
        }

      
        for (int i = sorted_n - 1; i >= 0; i--) {
            list2 = addfirst(list2, sorted_arr[i]);
        }

        free(sorted_arr);
    }

    printf("Sorted list:");
    printlist(list2);

    int insert_sorted_value;
    scanf("%d", &insert_sorted_value);

    printf("After sorted insertion:");
    list2 = insersort(list2, insert_sorted_value);
    printlist(list2);

    return 0;
}